"""Clear Hour ground-truth probe: OpenAQ v3 monitors near Rawalpindi/Islamabad vs CAMS. Re-runnable.

Usage: .venv/Scripts/python scripts/ground_truth_probe.py
Needs OPENAQ_API_KEY in .env. Writes results/ground_truth_probe.md (aggregates only).
Raw pulls cached in data/raw/openaq/ (git-ignored). CAMS series reused from scripts/aq_probe.py cache.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import aq_probe  # noqa: E402  (CAMS pull helpers + cache)

load_dotenv(ROOT / ".env")
API = "https://api.openaq.org/v3"
CACHE = ROOT / "data" / "raw" / "openaq"
LAT, LON = 33.6, 73.05
BBOX = "72.51,33.15,73.59,34.05"  # ~50 km each way from LAT, LON
EMBASSY_IDS = [8634, 233470]  # US Diplomatic Post Islamabad: StateAir feed, AirNow feed
N_LOWCOST = 3

session = requests.Session()
session.headers.update({"X-API-Key": os.environ.get("OPENAQ_API_KEY", ""),
                        "User-Agent": "field-window/0.1 (Clear Hour hackathon probe)"})
_last = 0.0
errors: list[str] = []


def get(path: str, params: dict | None = None, cache: bool = True) -> dict | None:
    """OpenAQ GET: >=1.1 s spacing (limit 60/min), backoff on 429/5xx/network, cached on disk."""
    global _last
    params = params or {}
    key = hashlib.sha1((path + json.dumps(params, sort_keys=True)).encode()).hexdigest()[:16]
    fp = CACHE / f"{key}.json"
    if cache and fp.exists():
        return json.loads(fp.read_text(encoding="utf-8"))
    for attempt in range(6):
        wait = 1.1 - (time.monotonic() - _last)
        if wait > 0:
            time.sleep(wait)
        try:
            r = session.get(f"{API}{path}", params=params, timeout=90)
        except requests.RequestException as e:
            _last = time.monotonic()
            time.sleep(2 ** attempt * 2)
            if attempt == 5:
                errors.append(f"{path} {params}: {type(e).__name__}")
            continue
        _last = time.monotonic()
        if r.status_code == 429 or r.status_code >= 500:
            reset = r.headers.get("X-Ratelimit-Reset")
            time.sleep(int(reset) + 1 if reset and reset.isdigit() else 2 ** attempt * 5)
            continue
        if not r.ok:
            errors.append(f"{path} {params}: HTTP {r.status_code} {r.text[:120]}")
            return None
        body = r.json()
        if cache:
            CACHE.mkdir(parents=True, exist_ok=True)
            fp.write_text(json.dumps(body), encoding="utf-8")
        return body
    return None


def km(lat1, lon1, lat2, lon2) -> float:
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 12742 * math.asin(math.sqrt(a))


def hours(sensor_id: int, start: date, end: date) -> pd.DataFrame:
    """Hourly averages for a sensor, paged, chunked by year. Index = hour-ending time in UTC."""
    rows = []
    y = start.year
    while y <= end.year:
        a, b = max(start, date(y, 1, 1)), min(end, date(y, 12, 31))
        # Past years are immutable -> cache; the current year is refetched.
        cache = b < date.today() - timedelta(days=2)
        page = 1
        while True:
            body = get(f"/sensors/{sensor_id}/hours", {"datetime_from": f"{a}T00:00:00Z",
                                                      "datetime_to": f"{b + timedelta(days=1)}T00:00:00Z",
                                                      "limit": 1000, "page": page}, cache=cache)
            res = (body or {}).get("results") or []
            for r in res:
                rows.append({"time": r["period"]["datetimeTo"]["utc"], "value": r["value"],
                             "pct": (r.get("coverage") or {}).get("percentComplete")})
            if len(res) < 1000:
                break
            page += 1
        y += 1
    if not rows:
        return pd.DataFrame(columns=["value", "pct"])
    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    return df.drop_duplicates("time").set_index("time").sort_index()


def clean(df: pd.DataFrame) -> pd.Series:
    s = df["value"].astype(float)
    return s[(s >= 0) & (s < 1500)]  # drop sentinel negatives (e.g. -999) and impossible spikes


def coverage_md(s: pd.Series, label: str) -> list[str]:
    if s.empty:
        return [f"**{label}**: no hourly data returned.", ""]
    grid = pd.date_range(s.index.min(), s.index.max(), freq="h")
    present = grid.isin(s.index)
    gap_list = aq_probe.gaps(pd.Series(~present), pd.Series(grid.tz_convert("Asia/Karachi").tz_localize(None)))
    out = [f"**{label}**", "",
           f"- Span (local, hour ending): {grid[0].tz_convert('Asia/Karachi'):%Y-%m-%d %H:%M} → "
           f"{grid[-1].tz_convert('Asia/Karachi'):%Y-%m-%d %H:%M}",
           f"- Valid hours: **{len(s)}** of {len(grid)} in span → **{100 * (1 - present.mean()):.1f}% missing**",
           f"- Gaps > 24 h: **{len(gap_list)}**, totalling {sum(n for *_, n in gap_list)} h", "",
           "| Year | Valid hours |", "|---|---|"]
    out += [f"| {y} | {n} |" for y, n in s.groupby(s.index.tz_convert('Asia/Karachi').year).size().items()]
    if gap_list:
        out += ["", "Longest gaps:"] + [f"- {a} → {b} ({n} h)" for a, b, n in sorted(gap_list, key=lambda g: -g[2])[:8]]
    return out + [""]


def compare_md(mon: pd.Series, cams: pd.Series, label: str) -> list[str]:
    """CAMS (instantaneous, local time) vs monitor hourly mean (hour ending, local)."""
    m = mon.copy()
    m.index = m.index.tz_convert("Asia/Karachi").tz_localize(None)
    out = [f"### CAMS vs {label}", ""]
    best = None
    lines = ["| Alignment | n | Pearson r |", "|---|---|---|"]
    for lag, desc in ((0, "CAMS at hour end"), (1, "CAMS at hour start"), (-1, "CAMS 1 h after end")):
        c = cams.copy()
        c.index = c.index + pd.Timedelta(hours=lag)
        j = pd.concat({"cams": c, "mon": m}, axis=1, join="inner").dropna()
        r = j["cams"].corr(j["mon"]) if len(j) > 2 else float("nan")
        lines.append(f"| {desc} | {len(j)} | {r:.3f} |")
        if lag == 0:
            best = j
    j = best
    if j is None or len(j) < 24:
        return out + ["Overlap too small (<24 h).", ""]
    err = j["cams"] - j["mon"]
    d = j.resample("D").mean().dropna()
    out += [f"- Overlap: **{len(j)} h** ({j.index.min():%Y-%m-%d} → {j.index.max():%Y-%m-%d})",
            f"- Hourly Pearson r: **{j['cams'].corr(j['mon']):.3f}**; Spearman: {j['cams'].corr(j['mon'], method='spearman'):.3f}",
            f"- Daily-mean Pearson r: **{d['cams'].corr(d['mon']):.3f}** (n={len(d)} days)",
            f"- Mean error (CAMS − monitor): **{err.mean():.1f} µg/m³**; MAE **{err.abs().mean():.1f}**; "
            f"monitor mean {j['mon'].mean():.1f}, CAMS mean {j['cams'].mean():.1f}",
            f"- Ratio monitor/CAMS (median of hourly ratios, CAMS>1): {(j['mon'] / j['cams'])[j['cams'] > 1].median():.2f}",
            "", "Alignment sensitivity:", "", *lines, ""]
    # Within-day ranking skill: does CAMS rank the hours of a day the way the monitor does?
    jj = j.copy()
    jj["day"] = jj.index.date
    full = jj.groupby("day").filter(lambda g: len(g) >= 20)
    rho = full.groupby("day").apply(lambda g: g["cams"].corr(g["mon"], method="spearman"))
    out += [f"- Within-day hour ranking (Spearman per day, days with ≥20 h, n={len(rho)}): "
            f"median **{rho.median():.2f}**, mean {rho.mean():.2f}", ""]
    jj["hour"] = jj.index.hour
    jj["season"] = ["Oct–Dec" if mth in (10, 11, 12) else "rest" for mth in jj.index.month]
    hb = jj.assign(err=err).groupby(["hour"]).agg(bias=("err", "mean"), mon=("mon", "mean"), cams=("cams", "mean"), n=("err", "size"))
    hs = jj.assign(err=err).groupby(["season", "hour"])["err"].mean().unstack(0)
    out += ["Bias by hour of day (local, hour ending), µg/m³:", "",
            "| Hour | n | Monitor mean | CAMS mean | Bias (CAMS−mon) | Bias Oct–Dec | Bias rest |", "|---|---|---|---|---|---|---|"]
    for h, r in hb.iterrows():
        out.append(f"| {h:02d} | {int(r.n)} | {r.mon:.1f} | {r.cams:.1f} | {r.bias:+.1f} | "
                   f"{hs.loc[h].get('Oct–Dec', float('nan')):+.1f} | {hs.loc[h].get('rest', float('nan')):+.1f} |")
    return out + [""]


def fetch_text(url: str) -> tuple[int | None, str]:
    try:
        r = requests.get(url, timeout=60, headers={"User-Agent": session.headers["User-Agent"]})
        r.encoding = "utf-8"
        return r.status_code, r.text
    except requests.RequestException as e:
        return None, str(e)


def main() -> None:
    if not os.environ.get("OPENAQ_API_KEY"):
        sys.exit("OPENAQ_API_KEY missing in .env")
    now = datetime.now(timezone.utc)
    today = now.date()
    md = ["# Clear Hour — ground-truth probe (OpenAQ v3)", "",
          f"Centre lat {LAT}, lon {LON}; bbox {BBOX} (~50 km). Run {now:%Y-%m-%d %H:%M} UTC by "
          "`scripts/ground_truth_probe.py`. Aggregates only.", ""]

    # 1) locations
    locs = (get("/locations", {"bbox": BBOX, "limit": 1000}, cache=False) or {}).get("results", [])
    for L in locs:
        L["_km"] = km(LAT, LON, L["coordinates"]["latitude"], L["coordinates"]["longitude"])
        L["_pm25"] = next((s["id"] for s in L["sensors"] if s["parameter"]["name"] == "pm25"), None)
    locs.sort(key=lambda L: (not L.get("isMonitor"), L["_km"]))
    md += ["## 1) Monitoring locations within ~50 km", "",
           f"OpenAQ returns **{len(locs)}** locations; **{sum(bool(L.get('isMonitor')) for L in locs)}** flagged "
           "reference-grade (`isMonitor=true`), the rest low-cost sensors.", "",
           "| id | Name | Lat, Lon | km | Grade | Provider | Parameters | First (UTC) | Last (UTC) |",
           "|---|---|---|---|---|---|---|---|---|"]
    for L in locs:
        md.append(f"| {L['id']} | {L['name'].strip().replace('|', '/')} | {L['coordinates']['latitude']:.4f}, "
                  f"{L['coordinates']['longitude']:.4f} | {L['_km']:.1f} | {'reference' if L.get('isMonitor') else 'low-cost'} | "
                  f"{(L.get('provider') or {}).get('name')} | {', '.join(s['parameter']['name'] for s in L['sensors'])} | "
                  f"{(L.get('datetimeFirst') or {}).get('utc', '')[:10]} | {(L.get('datetimeLast') or {}).get('utc', '')[:10]} |")
    md.append("")

    # 2) best PM2.5 series: US Embassy (two feeds merged), plus top low-cost candidates that are current
    by_id = {L["id"]: L for L in locs}
    series: dict[str, pd.Series] = {}
    md += ["## 2) Hourly PM2.5 coverage", ""]
    emb_parts = []
    for lid in EMBASSY_IDS:
        L = by_id.get(lid)
        if not L or not L["_pm25"]:
            md.append(f"- location {lid}: not found")
            continue
        s = clean(hours(L["_pm25"], date.fromisoformat(L["datetimeFirst"]["utc"][:10]),
                        date.fromisoformat(L["datetimeLast"]["utc"][:10])))
        series[f"{L['name']} [{lid}, {L['provider']['name']}]"] = s
        emb_parts.append(s)
    if emb_parts:
        merged = pd.concat(emb_parts).groupby(level=0).first().sort_index()  # StateAir first, AirNow fills
        series["US Embassy Islamabad — merged StateAir+AirNow"] = merged
        both = pd.concat(emb_parts, axis=1, join="inner").dropna()
        if len(both):
            md.append(f"- StateAir vs AirNow feeds, {len(both)} common hours: mean |diff| "
                      f"{(both.iloc[:, 0] - both.iloc[:, 1]).abs().mean():.2f} µg/m³ (same instrument, two feeds)")
            md.append("")
    cutoff = now - timedelta(days=3)
    lowcost = [L for L in locs if not L.get("isMonitor") and L["_pm25"] and L["_km"] <= 15
               and pd.Timestamp(L["datetimeLast"]["utc"]) >= cutoff]
    lowcost.sort(key=lambda L: L["datetimeFirst"]["utc"])
    for L in lowcost[:N_LOWCOST]:
        s = clean(hours(L["_pm25"], date.fromisoformat(L["datetimeFirst"]["utc"][:10]), today))
        series[f"{L['name'].strip()} [{L['id']}, {L['provider']['name']}, low-cost, {L['_km']:.1f} km]"] = s
    for label, s in series.items():
        md += coverage_md(s, label)

    # 3) recency
    md += ["## 3) Recency — last 7 days", "", "| Series | Hours in last 7 days (of 168) | Latest reading (local) | Age |",
           "|---|---|---|---|"]
    for label, s in series.items():
        last7 = s[s.index >= now - timedelta(days=7)]
        latest = s.index.max() if len(s) else None
        md.append(f"| {label} | {len(last7)} | {latest.tz_convert('Asia/Karachi'):%Y-%m-%d %H:%M} | "
                  f"{(now - latest).total_seconds() / 3600:.0f} h |" if latest is not None else f"| {label} | 0 | — | — |")
    lat_lc = [L for L in locs if L["_pm25"]]
    md += ["", "Latest-reading endpoint (`/locations/{id}/latest`) for the embassy + chosen low-cost sites:", ""]
    for L in [by_id[i] for i in EMBASSY_IDS if i in by_id] + lowcost[:N_LOWCOST]:
        res = (get(f"/locations/{L['id']}/latest", cache=False) or {}).get("results", [])
        pm = [r for r in res if r.get("sensorsId") == L["_pm25"]]
        md.append(f"- {L['id']} {L['name'].strip()}: " + (f"{pm[0]['value']} µg/m³ at {pm[0]['datetime']['local']}" if pm else "no pm25 latest"))
    md.append(f"- Current low-cost PM2.5 sites (last reading within 3 days, any distance ≤50 km): "
              f"**{sum(1 for L in lat_lc if not L.get('isMonitor') and pd.Timestamp(L['datetimeLast']['utc']) >= cutoff)}**; "
              f"current reference-grade sites: **{sum(1 for L in lat_lc if L.get('isMonitor') and pd.Timestamp(L['datetimeLast']['utc']) >= cutoff)}**")
    md.append("")

    # 4) CAMS comparison
    cams_df, _ = aq_probe.pull(aq_probe.AQ_URL, ["pm2_5"], date(2022, 8, 4), today - timedelta(days=1), months=3)
    cams = cams_df.set_index("time")["pm2_5"].dropna()
    cams = cams[~cams.index.normalize().isin(pd.to_datetime(["2022-12-14", "2022-12-15"]))]  # known CAMS artifact
    md += ["## 4) CAMS (Open-Meteo, 33.6, 73.05) vs monitors — overlap", "",
           "CAMS = instantaneous model value (local time); monitor = hourly mean, hour-ending, converted UTC→Asia/Karachi. "
           "CAMS artifact days 2022-12-14/15 excluded.", ""]
    for label, s in series.items():
        if "merged" in label or "low-cost" in label:
            md += compare_md(s, cams, label)

    # 5) licences / terms
    md += ["## 5) Licence / attribution", ""]
    for L in [by_id[i] for i in EMBASSY_IDS if i in by_id] + lowcost[:N_LOWCOST]:
        lic = L.get("licenses")
        md.append(f"- {L['id']} {L['name'].strip()} ({L['provider']['name']}): licenses field = "
                  + (", ".join(f"{x.get('name')} (attribution: {(x.get('attribution') or {}).get('name')}, "
                               f"{(x.get('attribution') or {}).get('url')}; from {x.get('dateFrom')})" for x in lic) if lic else "null"))
    lic_ids = {x["id"] for L in locs for x in (L.get("licenses") or [])}
    for lid in sorted(lic_ids):
        body = (get(f"/licenses/{lid}") or {}).get("results", [{}])[0]
        md.append(f"- licence {lid}: {body.get('name')} — commercial {body.get('commercialUseAllowed')}, "
                  f"attribution required {body.get('attributionRequired')}, share-alike {body.get('shareAlikeRequired')}, "
                  f"modification {body.get('modificationAllowed')}, redistribution {body.get('redistributionAllowed')}; {body.get('sourceUrl')}")
    md.append("")
    for url, words in (("https://docs.openaq.org/about/terms", ["licen", "attribut", "CC BY", "rate"]),
                       ("https://www.airnow.gov/airnow-data-exchange-guidelines/", ["attribut", "public domain", "preliminary", "not fully verified"]),
                       ("https://www.airgradient.com/open-data/", ["licen", "CC BY", "attribut"])):
        st, text = fetch_text(url)
        md.append(f"**{url}** (HTTP {st})")
        md.append("")
        sn = aq_probe.snippets(text, words) if st == 200 else []
        md += [f"> …{x}…" for x in sn[:6]] or ["> (no matching text found / page not fetched)"]
        md.append("")

    md += ["## Errors", ""] + ([f"- {e}" for e in errors] or ["- none"]) + [""]
    out = ROOT / "results" / "ground_truth_probe.md"
    out.write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    print(f"\nwrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
