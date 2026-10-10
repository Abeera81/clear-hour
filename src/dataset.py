"""Build the Clear Hour hourly dataset → data/processed/hourly.parquet.

One row per local hour where OpenAQ sensor 4554236 (Rawalpindi Women University, AirGradient,
uncalibrated low-cost) has a valid PM2.5 reading. Target y = monitor pm25.
Features are forecast-available only (CAMS, weather, calendar); no monitor reading is a feature.

Time convention: a row's `time` is the START of the local (Asia/Karachi, UTC+5) hour; y is the
monitor mean over [time, time+1h). CAMS values are instantaneous at `time`; the +1h shift is the
value at hour end.

Usage: .venv/Scripts/python -m src.dataset
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import aq_probe  # noqa: E402  (cached Open-Meteo pulls)
import ground_truth_probe as gt  # noqa: E402  (cached OpenAQ pulls)

SENSOR_LOCATION = 4554236
START = date(2025, 5, 29)
CAMS_ARTIFACT_DAYS = ["2022-12-14", "2022-12-15"]
OUT = ROOT / "data" / "processed" / "hourly.parquet"

CAMS_VARS = ["pm2_5", "pm10", "carbon_monoxide", "nitrogen_dioxide", "ozone", "sulphur_dioxide"]
WX_VARS = ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "wind_direction_10m",
           "pressure_msl", "precipitation", "boundary_layer_height"]


def monitor_series(end: date) -> pd.Series:
    loc = gt.get(f"/locations/{SENSOR_LOCATION}", cache=False)["results"][0]
    sid = next(s["id"] for s in loc["sensors"] if s["parameter"]["name"] == "pm25")
    s = gt.clean(gt.hours(sid, START, end))
    # OpenAQ hour-ending UTC → hour-start local
    s.index = (s.index - pd.Timedelta(hours=1)).tz_convert("Asia/Karachi").tz_localize(None)
    return s.rename("y")


def cams_frame(start: date, end: date) -> pd.DataFrame:
    df, _ = aq_probe.pull(aq_probe.AQ_URL, CAMS_VARS, start, end, months=3)
    df = df.set_index("time").sort_index()
    df = df.reindex(pd.date_range(df.index.min(), df.index.max(), freq="h"))
    p = df["pm2_5"]
    out = df.add_prefix("cams_")
    for k in (-3, -1, 1, 3):  # value k hours later (+) / earlier (-) within the CAMS series
        out[f"cams_pm2_5_{'p' if k > 0 else 'm'}{abs(k)}h"] = p.shift(-k)
    out["cams_pm2_5_roll24"] = p.rolling(24, min_periods=12).mean()
    out["cams_pm2_5_dayrank"] = p.groupby(p.index.date).rank(pct=True)
    return out


def weather_frame(start: date, end: date) -> pd.DataFrame:
    df, _ = aq_probe.pull(aq_probe.WX_URL, WX_VARS, start, end, months=12)
    df = df.set_index("time").sort_index()
    rad = np.deg2rad(df.pop("wind_direction_10m"))
    df["wind_dir_sin"], df["wind_dir_cos"] = np.sin(rad), np.cos(rad)
    return df.add_prefix("wx_")


def calendar_frame(idx: pd.DatetimeIndex) -> pd.DataFrame:
    doy = idx.dayofyear
    return pd.DataFrame({
        "hour": idx.hour, "dow": idx.dayofweek, "month": idx.month,
        "doy_sin": np.sin(2 * np.pi * doy / 365.25), "doy_cos": np.cos(2 * np.pi * doy / 365.25),
        "is_weekend": (idx.dayofweek >= 5).astype(int),
    }, index=idx)


def build() -> pd.DataFrame:
    end = date.today() - timedelta(days=1)
    y = monitor_series(end)
    # CAMS from 1 day earlier so lags/rolling are defined at the start.
    cams = cams_frame(START - timedelta(days=2), end)
    wx = weather_frame(START - timedelta(days=1), end)
    df = pd.concat([y], axis=1).join(cams, how="left").join(wx, how="left")
    df = df.join(calendar_frame(df.index))
    df = df[~df.index.normalize().isin(pd.to_datetime(CAMS_ARTIFACT_DAYS))]
    n0 = len(df)
    # Drop rows whose core inputs are missing (e.g. weather archive lags ~5 days behind today).
    core = ["cams_pm2_5", "cams_pm2_5_p1h", "wx_temperature_2m"]
    df = df.dropna(subset=core)
    df.index.name = "time"
    df.attrs["dropped_missing_core"] = n0 - len(df)
    return df


def feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c != "y"]


def main() -> None:
    df = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT)
    print(f"rows: {len(df)} ({df.index.min()} → {df.index.max()}); dropped for missing core inputs: "
          f"{df.attrs['dropped_missing_core']}")
    print(f"features ({len(feature_columns(df))}): {', '.join(feature_columns(df))}")
    print("missing % per feature:", (df.isna().mean() * 100).round(2)[lambda s: s > 0].to_dict())
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
