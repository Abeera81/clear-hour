"""Clear Hour data feasibility probe: Open-Meteo Air Quality + weather archive. Re-runnable.

Usage: .venv/Scripts/python scripts/aq_probe.py
Writes results/aq_probe.md (aggregates only). Raw pulls cached in data/raw/aq/ (git-ignored).
No modelling, no features.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "raw" / "aq"
AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WX_URL = "https://archive-api.open-meteo.com/v1/archive"
LAT, LON = 33.6, 73.05
POLLUTANTS = ["pm2_5", "pm10", "carbon_monoxide", "nitrogen_dioxide", "ozone", "sulphur_dioxide"]
WEATHER = ["temperature_2m", "wind_speed_10m", "wind_direction_10m", "pressure_msl",
           "boundary_layer_height", "relative_humidity_2m", "precipitation"]
UA = "field-window/0.1 (Clear Hour hackathon data probe; low volume)"

session = requests.Session()
session.headers["User-Agent"] = UA
_last = 0.0
errors: list[str] = []


def get(url: str, params: dict, cache: bool = True, raw: bool = False):
    """GET with >=1 s spacing, retries with backoff, optional on-disk cache. Returns (status, json|text)."""
    global _last
    key = hashlib.sha1((url + json.dumps(params, sort_keys=True)).encode()).hexdigest()[:16]
    path = CACHE / f"{key}.json"
    if cache and path.exists():
        return 200, json.loads(path.read_text(encoding="utf-8"))
    for attempt in range(5):
        wait = 1.0 - (time.monotonic() - _last)
        if wait > 0:
            time.sleep(wait)
        try:
            r = session.get(url, params=params, timeout=120)
        except requests.RequestException as e:
            _last = time.monotonic()
            time.sleep(2 ** attempt * 2)
            if attempt == 4:
                errors.append(f"{url} {params.get('start_date', '')}: {type(e).__name__}")
                return None, str(e)
            continue
        _last = time.monotonic()
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(2 ** attempt * 5)
            continue
        if raw:
            return r.status_code, r.text
        try:
            body = r.json()
        except ValueError:
            body = r.text
        if r.ok and cache:
            CACHE.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(body), encoding="utf-8")
        return r.status_code, body
    return r.status_code, r.text


def aq_day_has_pm25(d: date) -> bool:
    s, body = get(AQ_URL, {"latitude": LAT, "longitude": LON, "hourly": "pm2_5", "timezone": "auto",
                           "start_date": d.isoformat(), "end_date": d.isoformat()})
    if s != 200 or not isinstance(body, dict):
        return False
    return any(v is not None for v in body.get("hourly", {}).get("pm2_5", []))


def find_earliest(today: date) -> tuple[date, list[str]]:
    log = []
    good = today - timedelta(days=7)
    assert aq_day_has_pm25(good), "no pm2_5 even for last week"
    bad = None
    for y in range(today.year - 1, 1999, -1):
        d = date(y, 1, 1)
        ok = aq_day_has_pm25(d)
        log.append(f"{d}: {'data' if ok else 'no data'}")
        if ok:
            good = d
        else:
            bad = d
            break
    if bad is None:
        return good, log
    while (good - bad).days > 1:
        mid = bad + (good - bad) // 2
        ok = aq_day_has_pm25(mid)
        log.append(f"{mid}: {'data' if ok else 'no data'}")
        good, bad = (mid, bad) if ok else (good, mid)
    return good, log


def accepted_vars(candidates: list[str], url: str, d: date) -> tuple[list[str], dict[str, str]]:
    ok, rejected = [], {}
    for v in candidates:
        s, body = get(url, {"latitude": LAT, "longitude": LON, "hourly": v, "timezone": "auto",
                            "start_date": d.isoformat(), "end_date": d.isoformat()})
        if s == 200 and isinstance(body, dict) and "hourly" in body:
            ok.append(v)
        else:
            rejected[v] = (body.get("reason") if isinstance(body, dict) else str(body))[:120]
    return ok, rejected


def pull(url: str, variables: list[str], start: date, end: date, months: int) -> tuple[pd.DataFrame, dict]:
    frames, meta = [], {}
    cur = start
    while cur <= end:
        nxt = min((pd.Timestamp(cur) + pd.DateOffset(months=months)).date() - timedelta(days=1), end)
        s, body = get(url, {"latitude": LAT, "longitude": LON, "hourly": ",".join(variables),
                            "timezone": "auto", "start_date": cur.isoformat(), "end_date": nxt.isoformat()})
        if s == 200 and isinstance(body, dict):
            meta = {k: body.get(k) for k in ("timezone", "utc_offset_seconds", "latitude", "longitude", "elevation")}
            frames.append(pd.DataFrame(body["hourly"]))
        else:
            errors.append(f"pull {url} {cur}..{nxt}: HTTP {s} {str(body)[:120]}")
        cur = nxt + timedelta(days=1)
    df = pd.concat(frames, ignore_index=True)
    df["time"] = pd.to_datetime(df["time"])
    return df.drop_duplicates("time").sort_values("time").reset_index(drop=True), meta


def gaps(mask: pd.Series, times: pd.Series, min_hours: int = 24) -> list[tuple[str, str, int]]:
    out, start, n = [], None, 0
    for t, m in zip(times, mask):
        if m:
            start = start if start is not None else t
            n += 1
        else:
            if n > min_hours:
                out.append((str(start), str(t - pd.Timedelta(hours=1)), n))
            start, n = None, 0
    if n > min_hours:
        out.append((str(start), str(times.iloc[-1]), n))
    return out


def snippets(text: str, words: list[str], width: int = 220) -> list[str]:
    plain = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.S)
    plain = re.sub(r"<[^>]+>", " ", plain)
    plain = re.sub(r"&nbsp;|&#160;", " ", plain)
    plain = re.sub(r"\s+", " ", plain)
    out = []
    for w in words:
        for m in re.finditer(re.escape(w), plain, flags=re.I):
            s = plain[max(0, m.start() - width // 2): m.end() + width // 2].strip()
            if not any(s[:60] in o for o in out):
                out.append(s)
            if len(out) > 40:
                return out
    return out


def main() -> None:
    today = date.today()
    md = ["# Clear Hour — air-quality data feasibility probe", "",
          f"Location lat {LAT}, lon {LON} (Rawalpindi/Islamabad), timezone=auto. "
          f"Run {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} by `scripts/aq_probe.py`. Aggregates only.", ""]

    # 1) history depth
    earliest, log = find_earliest(today)
    md += ["## 1) History depth", "", f"Earliest date with hourly pm2_5: **{earliest}**", "",
           "Search log (year steps, then binary search):", "", "```", *log, "```", ""]

    # 2) coverage
    aq_vars, aq_rej = accepted_vars(POLLUTANTS, AQ_URL, today - timedelta(days=7))
    end = today - timedelta(days=1)
    aq, aq_meta = pull(AQ_URL, aq_vars, earliest, end, months=3)
    full_idx = pd.date_range(aq["time"].min(), aq["time"].max(), freq="h")
    missing_ts = len(full_idx.difference(aq["time"]))
    md += ["## 2) Coverage", "", f"Span {aq['time'].min()} → {aq['time'].max()} ({aq_meta.get('timezone')}, "
           f"UTC offset {aq_meta.get('utc_offset_seconds')} s; grid point {aq_meta.get('latitude')}, {aq_meta.get('longitude')})", "",
           f"- Variables accepted: {', '.join(aq_vars)}",
           f"- Variables rejected: {', '.join(f'{k} ({v})' for k, v in aq_rej.items()) or 'none'}",
           f"- Total hourly rows: **{len(aq)}** (timestamps missing from the hourly grid: {missing_ts})", "",
           "| Variable | % missing (null) |", "|---|---|"]
    md += [f"| {v} | {100 * aq[v].isna().mean():.2f}% |" for v in aq_vars]
    md += ["", "| Year | Rows | pm2_5 non-null |", "|---|---|---|"]
    for y, g in aq.groupby(aq["time"].dt.year):
        md.append(f"| {y} | {len(g)} | {g['pm2_5'].notna().sum()} |")
    g24 = gaps(aq["pm2_5"].isna(), aq["time"])
    md += ["", f"Gaps in pm2_5 longer than 24 h: **{len(g24)}**"]
    md += [f"- {a} → {b} ({n} h)" for a, b, n in g24[:20]]
    md.append("")

    # 3) seasonal / diurnal
    pm = aq.dropna(subset=["pm2_5"]).copy()
    pm["month"], pm["hour"] = pm["time"].dt.month, pm["time"].dt.hour
    by_month = pm.groupby("month")["pm2_5"].mean()
    md += ["## 3) Seasonal / diurnal shape (pm2_5, µg/m³)", "", "| Month | Mean pm2_5 | Hours |", "|---|---|---|"]
    md += [f"| {m} | {v:.1f} | {(pm['month'] == m).sum()} |" for m, v in by_month.items()]
    smog = pm["month"].isin([10, 11, 12])
    h_smog = pm[smog].groupby("hour")["pm2_5"].mean()
    h_rest = pm[~smog].groupby("hour")["pm2_5"].mean()
    md += ["", "| Hour (local) | Oct–Dec mean | Rest-of-year mean |", "|---|---|---|"]
    md += [f"| {h:02d} | {h_smog.get(h, float('nan')):.1f} | {h_rest.get(h, float('nan')):.1f} |" for h in range(24)]
    md.append("")
    for name, s in (("Oct–Dec", h_smog), ("Rest of year", h_rest)):
        md.append(f"- {name}: min hour {s.idxmin():02d}h ({s.min():.1f}), max hour {s.idxmax():02d}h ({s.max():.1f}), "
                  f"max/min ratio **{s.max() / s.min():.2f}**")
    md.append("")

    # 4) forecast endpoint
    md += ["## 4) Forecast endpoint", ""]
    for fd in (5, 7, 16):
        s, body = get(AQ_URL, {"latitude": LAT, "longitude": LON, "hourly": "pm2_5", "timezone": "auto",
                               "forecast_days": fd}, cache=False)
        if s == 200 and isinstance(body, dict):
            f = pd.DataFrame(body["hourly"])
            f["time"] = pd.to_datetime(f["time"])
            nn = f.dropna(subset=["pm2_5"])
            md.append(f"- forecast_days={fd}: HTTP 200, {len(f)} rows, non-null pm2_5 through **{nn['time'].max()}** "
                      f"({nn['time'].dt.date.nunique()} calendar days incl. today)")
        else:
            md.append(f"- forecast_days={fd}: HTTP {s} — {(body.get('reason') if isinstance(body, dict) else str(body))[:150]}")
    s, body = get(AQ_URL, {"latitude": LAT, "longitude": LON, "hourly": "pm2_5", "timezone": "auto",
                           "past_days": 3, "forecast_days": 1}, cache=False)
    if s == 200 and isinstance(body, dict):
        f = pd.DataFrame(body["hourly"])
        f["time"] = pd.to_datetime(f["time"])
        past = f[f["time"].dt.date < today]
        md.append(f"- past_days=3: HTTP 200, {len(past)} past hours, {past['pm2_5'].notna().sum()} non-null "
                  f"({past['time'].min()} → {past['time'].max()})")
        # Compare past_days values against the archived values pulled in step 2 for the same hours.
        j = past.merge(aq[["time", "pm2_5"]], on="time", suffixes=("_pastdays", "_history")).dropna()
        if len(j):
            diff = (j["pm2_5_pastdays"] - j["pm2_5_history"]).abs()
            md.append(f"- past_days vs history pull, {len(j)} overlapping hours: mean |diff| {diff.mean():.2f}, max {diff.max():.2f}")
    else:
        md.append(f"- past_days=3: HTTP {s} — {str(body)[:150]}")
    md.append("")

    # 5) weather join
    wx_end = today - timedelta(days=6)  # archive lags a few days
    wx_vars, wx_rej = accepted_vars(WEATHER, WX_URL, wx_end)
    wx, wx_meta = pull(WX_URL, wx_vars, earliest, wx_end, months=12)
    joined = aq.merge(wx, on="time", how="inner")
    overlap = aq[(aq["time"] >= wx["time"].min()) & (aq["time"] <= wx["time"].max())]
    md += ["## 5) Weather join (Open-Meteo archive)", "",
           f"- Variables accepted: {', '.join(wx_vars)}",
           f"- Variables rejected: {', '.join(f'{k} ({v})' for k, v in wx_rej.items()) or 'none'}",
           f"- Weather span {wx['time'].min()} → {wx['time'].max()}, {len(wx)} rows; timezone {wx_meta.get('timezone')}, "
           f"UTC offset {wx_meta.get('utc_offset_seconds')} s (AQ: {aq_meta.get('timezone')}, {aq_meta.get('utc_offset_seconds')} s)",
           f"- AQ rows inside weather span: {len(overlap)}; matched on identical timestamp: **{len(joined)}** "
           f"({100 * len(joined) / max(len(overlap), 1):.2f}%)", "",
           "| Weather variable | % missing in joined rows |", "|---|---|"]
    md += [f"| {v} | {100 * joined[v].isna().mean():.2f}% |" for v in wx_vars]
    md.append("")
    for v in wx_vars:
        for a, b, n in gaps(wx[v].isna(), wx["time"], min_hours=0)[:5]:
            md.append(f"- {v} null block: {a} → {b} ({n} h)")
    md.append("")

    # 6) license / attribution
    md += ["## 6) License / attribution (verbatim snippets from fetched pages)", ""]
    for url, words in (("https://open-meteo.com/en/docs/air-quality-api", ["CAMS", "Copernicus", "licen", "attribution"]),
                       ("https://open-meteo.com/en/licence", ["CC BY 4.0", "Attribution", "Weather data by", "air quality"]),
                       ("https://open-meteo.com/en/terms", ["non-commercial", "10,000", "10000", "calls", "fair"])):
        s, text = get(url, {}, cache=False, raw=True)
        md.append(f"**{url}** (HTTP {s})")
        md.append("")
        sn = snippets(text, words) if s == 200 else []
        md += [f"> …{x}…" for x in sn[:10]] or ["> (no matching text found)"]
        md.append("")

    # 7) sanity
    daily = pm.groupby(pm["time"].dt.date)["pm2_5"].agg(["mean", "count"])
    daily = daily[daily["count"] >= 20]
    md += ["## 7) Sanity — daily-mean pm2_5 extremes (days with ≥20 h)", "", "| Rank | Highest day | Mean | Lowest day | Mean |",
           "|---|---|---|---|---|"]
    hi, lo = daily["mean"].nlargest(5), daily["mean"].nsmallest(5)
    for i in range(5):
        md.append(f"| {i + 1} | {hi.index[i]} | {hi.iloc[i]:.1f} | {lo.index[i]} | {lo.iloc[i]:.1f} |")
    sus = daily[daily["mean"] < 3]
    md += ["", f"Suspected upstream artifacts (daily mean pm2_5 < 3 µg/m³, implausible for this city): "
           f"**{', '.join(str(d) for d in sus.index) or 'none'}**", ""]
    md += ["## Caveats", "",
           "- Source is the CAMS **model** (global domain here: 0.4° ≈ 45 km grid, 3-hourly upstream, "
           "interpolated to hourly by Open-Meteo), not ground-station measurements. `past_days` returns the "
           "same model series as the history pull (see §4), so scoring a forecast against it scores against CAMS, "
           "not against measured air.",
           "- Diurnal shape partly reflects CAMS model chemistry/BLH dynamics at 45 km, not a single street.", ""]
    md += ["## Errors", ""] + ([f"- {e}" for e in errors] or ["- none"]) + [""]

    out = ROOT / "results" / "aq_probe.md"
    out.write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    print(f"\nwrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
