"""Pre-registered Clear Hour forecast for one local day (Asia/Karachi) from LIVE forecast endpoints.

Usage: .venv/Scripts/python -m src.forecast 2026-10-11 [stage1|stage2]
  stage1: writes B0 raw CAMS + B2 hour-bias forecast (fast) -> commit immediately
  stage2: fits TabPFN v2 (slow, ~85 min CPU), rewrites card with all three models

Features mirror src/dataset.py exactly; inputs come from the forecast endpoints, not the archives.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import dataset as ds  # noqa: E402

AQ = "https://air-quality-api.open-meteo.com/v1/air-quality"
WX = "https://api.open-meteo.com/v1/forecast"
UA = {"User-Agent": "field-window/0.1 (Clear Hour hackathon)"}
TABPFN_ROWS = 10_000


def fetch(url: str, variables: list[str], past: int = 3, ahead: int = 4) -> pd.DataFrame:
    r = requests.get(url, params={"latitude": ds.aq_probe.LAT, "longitude": ds.aq_probe.LON, "hourly": ",".join(variables),
                                  "timezone": "Asia/Karachi", "past_days": past, "forecast_days": ahead},
                     headers=UA, timeout=60)
    r.raise_for_status()
    df = pd.DataFrame(r.json()["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    return df.set_index("time")


def live_features(day: str) -> tuple[pd.DataFrame, dict]:
    cams = fetch(AQ, ds.CAMS_VARS)
    wx = fetch(WX, ds.WX_VARS)
    meta = {"cams_span": [str(cams.index.min()), str(cams.index.max())], "wx_span": [str(wx.index.min()), str(wx.index.max())],
            "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    p = cams["pm2_5"]
    c = cams.add_prefix("cams_")
    for k in (-3, -1, 1, 3):
        c[f"cams_pm2_5_{'p' if k > 0 else 'm'}{abs(k)}h"] = p.shift(-k)
    c["cams_pm2_5_roll24"] = p.rolling(24, min_periods=12).mean()
    c["cams_pm2_5_dayrank"] = p.groupby(p.index.date).rank(pct=True)
    rad = np.deg2rad(wx.pop("wind_direction_10m"))
    wx["wind_dir_sin"], wx["wind_dir_cos"] = np.sin(rad), np.cos(rad)
    wx = wx.add_prefix("wx_")
    df = c.join(wx, how="left").join(ds.calendar_frame(c.index))
    d = pd.Timestamp(day)
    df = df[(df.index >= d) & (df.index < d + pd.Timedelta(days=1))]
    return df, meta


def windows(pred: pd.Series) -> dict:
    w = (pred + pred.shift(-1)) / 2
    w = w.dropna()
    lo, hi = w.idxmin(), w.idxmax()
    return {"cleanest": {"start": f"{lo:%H:%M}", "end": f"{lo + pd.Timedelta(hours=2):%H:%M}", "pm25": round(float(w[lo]), 1)},
            "dirtiest": {"start": f"{hi:%H:%M}", "end": f"{hi + pd.Timedelta(hours=2):%H:%M}", "pm25": round(float(w[hi]), 1)}}


def card(day: str, out: dict) -> str:
    now_utc = datetime.fromisoformat(out["generated_utc"])
    local = now_utc.astimezone(pd.Timestamp(day, tz="Asia/Karachi").tz)
    models = out["models"]
    primary = "M1 TabPFN v2" if "M1 TabPFN v2" in models else "B2 CAMS+hour bias"
    w = models[primary]["windows"]
    L = [f"# Clear Hour — pre-registered forecast for {day} (Asia/Karachi)", "",
         f"Generated {out['generated_utc']} UTC / {local:%Y-%m-%d %H:%M} local (Asia/Karachi, UTC+5). Stage: **{out['stage']}**.", "",
         f"> **Clear Hour predicts the cleanest 2h window of {day} is {w['cleanest']['start']}-{w['cleanest']['end']} at "
         f"{w['cleanest']['pm25']} ug/m3; the dirtiest is {w['dirtiest']['start']}-{w['dirtiest']['end']} at {w['dirtiest']['pm25']} ug/m3.**",
         f"> (model: {primary}; predicted hourly PM2.5 at OpenAQ sensor 4554236, Rawalpindi Women University)", "",
         "## Windows chosen by each model (2 consecutive hours, mean predicted µg/m³)", "",
         "| Model | Cleanest 2h | Dirtiest 2h |", "|---|---|---|"]
    for k, m in models.items():
        c, d = m["windows"]["cleanest"], m["windows"]["dirtiest"]
        L.append(f"| {k} | {c['start']}-{c['end']} ({c['pm25']}) | {d['start']}-{d['end']} ({d['pm25']}) |")
    names = list(models)
    L += ["", "## Predicted PM2.5 per hour (µg/m³, hour starting at)", "", "| Hour | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for i in range(24):
        L.append(f"| {i:02d}:00 | " + " | ".join(f"{models[n]['hourly'][i]:.1f}" for n in names) + " |")
    L += ["", "## Inputs and caveats", ""] + [f"- {x}" for x in out["caveats"]]
    return "\n".join(L) + "\n"


def main() -> None:
    day = sys.argv[1] if len(sys.argv) > 1 else "2026-10-11"
    stage = sys.argv[2] if len(sys.argv) > 2 else "stage2"
    live, meta = live_features(day)
    assert len(live) == 24, f"expected 24 hours, got {len(live)}"
    feats = [c for c in pd.read_parquet(ds.OUT).columns if c != "y"]
    missing = [f for f in feats if f not in live.columns]
    nulls = {f: int(live[f].isna().sum()) for f in feats if f in live.columns and live[f].isna().any()}
    assert not missing, f"features missing from live data: {missing}"

    # training data up to the day before, rebuilt now so the latest sensor hours are included
    train = ds.build()
    train = train[train.index < pd.Timestamp(day)]
    resid = train["y"] - train["cams_pm2_5"]
    hb = resid.groupby(train.index.hour).mean()
    cutoff = f"{train.index.max()}"

    caveats = [
        "Inputs are LIVE forecasts from the Open-Meteo air-quality and weather forecast endpoints (not the archives); "
        "the evaluation used archive inputs, so live skill is expected to be worse.",
        "Ground truth is an uncalibrated low-cost AirGradient sensor (OpenAQ 4554236; CC BY 4.0, The Urban Unit), not a reference monitor.",
        "On the held-out TEST month the exact cleanest-window hit rate (both hours inside the actual cleanest 6) was 37% for TabPFN v2 (30% raw CAMS, 43% B2).",
        f"Feature coverage: all {len(feats)} features built from the forecast endpoints; none substituted from archives. "
        f"Fill/null report: {'none' if not nulls else nulls}. Forecast CAMS grid point 33.6, 73.100006.",
        "Known differences vs training: training CAMS/weather were archive values; here CAMS comes from the forecast endpoint "
        "(`cams_pm2_5_roll24` and lags use the 3 past days + forecast of the same endpoint), weather from api.open-meteo.com/v1/forecast "
        "(`boundary_layer_height` is a model forecast; in training it was archive).",
        f"Training data: monitor hours up to {cutoff} ({len(train)} rows); B2 bias offsets fitted on all of it; TabPFN uses the most recent {TABPFN_ROWS}.",
    ]
    out = {"day": day, "stage": stage, "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "input_meta": meta, "train_rows": len(train), "train_last_hour": cutoff, "models": {}, "caveats": caveats,
           "feature_nulls": nulls, "inputs_hourly": live[["cams_pm2_5", "wx_temperature_2m", "wx_boundary_layer_height"]].round(2).to_dict("list")}
    idx = live.index
    b0 = live["cams_pm2_5"]
    b2 = b0 + idx.hour.map(hb).fillna(resid.mean()).to_numpy()
    for name, s in (("B0 raw CAMS", b0), ("B2 CAMS+hour bias", pd.Series(b2, index=idx))):
        s = pd.Series(np.asarray(s), index=idx)
        out["models"][name] = {"hourly": [round(float(x), 1) for x in s], "windows": windows(s)}

    def write(stage_name: str) -> None:
        out["stage"] = stage_name
        (ROOT / "results" / f"forecast_{day}.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
        (ROOT / "results" / f"forecast_{day}.md").write_text(card(day, out), encoding="utf-8")
        print(f"wrote forecast_{day}.* stage={stage_name}", flush=True)

    write("stage1 (B0 + B2 only; TabPFN fit in progress)")
    if stage == "stage1":
        return

    from tabpfn import TabPFNRegressor
    from tabpfn.constants import ModelVersion
    tr = train.iloc[-TABPFN_ROWS:]
    t = time.time()
    m = TabPFNRegressor.create_default_for_version(ModelVersion.V2, device="cpu", fit_mode="fit_with_cache",
                                                   ignore_pretraining_limits=True, random_state=0)
    m.fit(tr[feats], tr["y"].to_numpy())
    p = pd.Series(m.predict(live[feats]), index=idx)
    out["tabpfn"] = {"model_path": Path(str(m.model_path)).name, "train_rows": len(tr), "seconds": round(time.time() - t)}
    out["models"] = {"M1 TabPFN v2": {"hourly": [round(float(x), 1) for x in p], "windows": windows(p)}, **out["models"]}
    out["generated_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    write("stage2 (all three models)")


if __name__ == "__main__":
    main()
