"""Score a pre-registered forecast against measured PM2.5 from OpenAQ sensor 4554236.

Usage: .venv/Scripts/python scripts/score_forecast.py 2026-10-11
Reads results/forecast_<date>.json, pulls the day's measured hourly PM2.5 (Asia/Karachi), writes
results/forecast_<date>_score.md. Run only after the day is complete (sensor data lands with some delay).
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ground_truth_probe as gt  # noqa: E402

LOCATION_ID = 4554236
MIN_HOURS = 20


def measured(day: str) -> pd.Series:
    loc = gt.get(f"/locations/{LOCATION_ID}", cache=False)["results"][0]
    sid = next(s["id"] for s in loc["sensors"] if s["parameter"]["name"] == "pm25")
    d = date.fromisoformat(day)
    s = gt.clean(gt.hours(sid, d - timedelta(days=1), d + timedelta(days=1)))
    s.index = (s.index - pd.Timedelta(hours=1)).tz_convert("Asia/Karachi").tz_localize(None)  # hour-start, local
    start = pd.Timestamp(day)
    return s[(s.index >= start) & (s.index < start + pd.Timedelta(days=1))]


def score(day: str) -> str:
    fc = json.loads((ROOT / "results" / f"forecast_{day}.json").read_text(encoding="utf-8"))
    y = measured(day)
    idx = pd.date_range(day, periods=24, freq="h")
    y = y.reindex(idx)
    n = int(y.notna().sum())
    L = [f"# Score — forecast for {day}", "",
         f"Forecast file generated {fc['generated_utc']} UTC (stage: {fc['stage']}). Truth: OpenAQ sensor {LOCATION_ID} "
         f"(uncalibrated low-cost AirGradient, CC BY 4.0, The Urban Unit), hourly means, Asia/Karachi. "
         f"Measured hours available: **{n}/24**.", ""]
    if n < MIN_HOURS:
        return "\n".join(L + [f"Fewer than {MIN_HOURS} measured hours; per-day ranking metrics not computed."])
    day_mean = float(y.mean())
    clean6 = set(y.nsmallest(6).index)
    ok = y.notna() & y.shift(-1).notna()
    wy = ((y + y.shift(-1)) / 2)[ok]
    best_possible, worst_possible = float(wy.min()), float(wy.max())
    L += [f"Actual day mean **{day_mean:.1f}** µg/m³; best possible 2h window {best_possible:.1f} "
          f"({wy.idxmin():%H:%M}-{wy.idxmin() + pd.Timedelta(hours=2):%H:%M}); worst possible {worst_possible:.1f} "
          f"({wy.idxmax():%H:%M}). Actual cleanest 6 hours: {', '.join(f'{t:%H}h' for t in sorted(clean6))}.", "",
          "| Model | MAE | Bias | Within-day Spearman | Chosen cleanest 2h | Actual PM2.5 of that window | vs day mean | "
          "Window inside actual cleanest 6h? | Chosen dirtiest 2h | Actual PM2.5 of that window |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for name, m in fc["models"].items():
        p = pd.Series(m["hourly"], index=idx)
        both = pd.concat([p, y], axis=1, keys=["p", "y"]).dropna()
        err = both["p"] - both["y"]
        rho = both["p"].corr(both["y"], method="spearman")
        cw, dw = m["windows"]["cleanest"], m["windows"]["dirtiest"]
        cs, ds_ = pd.Timestamp(f"{day} {cw['start']}"), pd.Timestamp(f"{day} {dw['start']}")
        c_hours = {cs, cs + pd.Timedelta(hours=1)}
        d_hours = [ds_, ds_ + pd.Timedelta(hours=1)]
        c_act = y.reindex(sorted(c_hours)).mean()
        d_act = y.reindex(d_hours).mean() if all(h in y.index for h in d_hours) else float("nan")
        hit = c_hours <= clean6
        L.append(f"| {name} | {err.abs().mean():.1f} | {err.mean():+.1f} | {rho:.3f} | {cw['start']}-{cw['end']} | "
                 f"{c_act:.1f} | {c_act - day_mean:+.1f} | {'YES' if hit else 'no'} | {dw['start']}-{dw['end']} | {d_act:.1f} |")
    L += ["", "Notes: MAE/Bias in µg/m³ (pred − actual). Spearman over the hours that have a measurement. "
          "'Window inside actual cleanest 6h' requires both hours of the chosen 2h window to be among the day's 6 lowest measured hours. "
          "One day is one sample; do not read skill into a single result."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    day = sys.argv[1]
    out = ROOT / "results" / f"forecast_{day}_score.md"
    text = score(day)
    out.write_text(text, encoding="utf-8")
    print(text)
