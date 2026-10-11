"""Score a pre-registered forecast against measured PM2.5 from OpenAQ sensor 4554236.

Usage: .venv/Scripts/python scripts/score_forecast.py 2026-10-11 [--from-hour HH]
Reads results/forecast_<date>.json, pulls the day's measured hourly PM2.5 (Asia/Karachi), writes
results/forecast_<date>_score.md. Run only after the day is complete (sensor data lands with some delay).

Two tables: the full day, and only hours >= HH (the late-entry view: hours before a model's commit time had
already occurred and are not pre-registered). HH defaults to the stage-2 commit hour rounded up (read from the
forecast JSON's `late_entry.from_hour`, else the ceiling of the local hour of `generated_utc` for a stage-2 file,
else 0). In the >= HH view each model's cleanest/dirtiest 2h window is re-derived from its own predicted hours
>= HH, because its original pick may lie in hours that had already passed.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ground_truth_probe as gt  # noqa: E402

LOCATION_ID = 4554236
MIN_HOURS = 20
MIN_HOURS_PARTIAL = 4


def measured(day: str) -> pd.Series:
    loc = gt.get(f"/locations/{LOCATION_ID}", cache=False)["results"][0]
    sid = next(s["id"] for s in loc["sensors"] if s["parameter"]["name"] == "pm25")
    d = date.fromisoformat(day)
    s = gt.clean(gt.hours(sid, d - timedelta(days=1), d + timedelta(days=1)))
    s.index = (s.index - pd.Timedelta(hours=1)).tz_convert("Asia/Karachi").tz_localize(None)  # hour-start, local
    start = pd.Timestamp(day)
    return s[(s.index >= start) & (s.index < start + pd.Timedelta(days=1))]


def default_from_hour(fc: dict) -> int:
    le = fc.get("late_entry")
    if le and "from_hour" in le:
        return int(le["from_hour"])
    if str(fc.get("stage", "")).startswith("stage2"):
        t = datetime.fromisoformat(fc["generated_utc"]) + timedelta(hours=5)  # Asia/Karachi = UTC+5
        return min(24, math.ceil(t.hour + t.minute / 60 + t.second / 3600))
    return 0


def best_pair(s: pd.Series, low: bool) -> tuple[pd.Timestamp, float] | None:
    w = ((s + s.shift(-1)) / 2).dropna()
    if w.empty:
        return None
    t = w.idxmin() if low else w.idxmax()
    return t, float(w[t])


def table(fc: dict, y: pd.Series, idx: pd.DatetimeIndex, from_hour: int, rederive: bool) -> list[str]:
    sel = idx[idx.hour >= from_hour]
    ys = y.reindex(sel)
    n = int(ys.notna().sum())
    if n < (MIN_HOURS if from_hour == 0 else MIN_HOURS_PARTIAL):
        return [f"Only {n} measured hours in this view; metrics not computed.", ""]
    day_mean = float(ys.mean())
    clean_n = 6 if from_hour == 0 else max(2, round(6 * len(sel) / 24))
    clean = set(ys.nsmallest(clean_n).index)
    wy = ((ys + ys.shift(-1)) / 2).dropna()
    L = [f"Hours {from_hour:02d}:00-23:59, {n} measured. Actual mean **{day_mean:.1f}** µg/m³; best possible 2h window "
         f"{wy.min():.1f} ({wy.idxmin():%H:%M}); worst {wy.max():.1f} ({wy.idxmax():%H:%M}). "
         f"'Cleanest set' = the {clean_n} lowest measured hours in this view: {', '.join(f'{t:%H}h' for t in sorted(clean))}.", "",
         "| Model | MAE | Bias | Spearman | Chosen cleanest 2h | Actual PM2.5 there | vs mean | Inside cleanest set? | Chosen dirtiest 2h | Actual there |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for name, m in fc["models"].items():
        p = pd.Series(m["hourly"], index=idx).reindex(sel)
        both = pd.concat([p, ys], axis=1, keys=["p", "y"]).dropna()
        err = both["p"] - both["y"]
        rho = both["p"].corr(both["y"], method="spearman") if len(both) > 2 else float("nan")
        if rederive:
            c, d = best_pair(p, True), best_pair(p, False)
            cs, ds_ = (c[0] if c else None), (d[0] if d else None)
        else:
            cs = pd.Timestamp(f"{fc['day']} {m['windows']['cleanest']['start']}")
            ds_ = pd.Timestamp(f"{fc['day']} {m['windows']['dirtiest']['start']}")
        if cs is None or ds_ is None:
            continue
        ch, dh = [cs, cs + pd.Timedelta(hours=1)], [ds_, ds_ + pd.Timedelta(hours=1)]
        c_act, d_act = y.reindex(ch).mean(), y.reindex(dh).mean()
        L.append(f"| {name} | {err.abs().mean():.1f} | {err.mean():+.1f} | {rho:.3f} | {cs:%H:%M}-{ch[1] + pd.Timedelta(hours=1):%H:%M} | "
                 f"{c_act:.1f} | {c_act - day_mean:+.1f} | {'YES' if set(ch) <= clean else 'no'} | "
                 f"{ds_:%H:%M}-{dh[1] + pd.Timedelta(hours=1):%H:%M} | {d_act:.1f} |")
    return L + [""]


def score(day: str, from_hour: int | None) -> str:
    fc = json.loads((ROOT / "results" / f"forecast_{day}.json").read_text(encoding="utf-8"))
    fc["day"] = day
    fh = default_from_hour(fc) if from_hour is None else from_hour
    y = measured(day)
    idx = pd.date_range(day, periods=24, freq="h")
    n = int(y.reindex(idx).notna().sum())
    L = [f"# Score — forecast for {day}", "",
         f"Forecast file generated {fc['generated_utc']} UTC (stage: {fc['stage']}). Truth: OpenAQ sensor {LOCATION_ID} "
         f"(uncalibrated low-cost AirGradient, CC BY 4.0, The Urban Unit), hourly means, Asia/Karachi. Measured hours: **{n}/24**.", ""]
    if fc.get("late_entry"):
        L += [f"> {fc['late_entry']['statement']}", ""]
    if n < MIN_HOURS_PARTIAL:
        return "\n".join(L + ["Too few measured hours to score."])
    L += ["## Full day (all 24 hours)", ""] + table(fc, y, idx, 0, rederive=False)
    if fh > 0:
        L += [f"## Hours >= {fh:02d}:00 only (late-entry view; windows re-derived from each model's own predictions in this range)", ""]
        L += table(fc, y, idx, fh, rederive=True)
    L += ["Notes: MAE/Bias in µg/m³ (pred − actual); Spearman over measured hours in the view. "
          "'Inside cleanest set' needs both hours of the 2h window among the view's lowest measured hours. "
          "One day is one sample; do not read skill into a single result."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("day")
    ap.add_argument("--from-hour", type=int, default=None, metavar="HH", help="also score hours >= HH (default: stage-2 commit hour, rounded up)")
    a = ap.parse_args()
    text = score(a.day, a.from_hour)
    (ROOT / "results" / f"forecast_{a.day}_score.md").write_text(text, encoding="utf-8")
    print(text)
