"""Clear Hour forecast engine: live inputs -> 26 features -> B0 / B2 / TabPFN v2 predictions for one local day.

Shared by the CLI (`python -m clearhour`) and by the pre-registration runner below:
  .venv/Scripts/python -m src.forecast 2026-10-11 [stage1|stage2]
    stage1: writes B0 + B2 (fast) -> commit immediately;  stage2: also fits TabPFN v2 (~40 min CPU for 10,000 rows).

Features mirror src/dataset.py exactly; inputs come from the forecast endpoints, not the archives.
Never run this runner for a date whose results/forecast_<date>.* is already committed: it overwrites those files.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
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
LOCAL_OFFSET = timedelta(hours=5)  # Asia/Karachi has no DST
MAX_AHEAD_DAYS = 7  # Open-Meteo air-quality forecast_days limit
PACKAGED_B2 = ROOT / "src" / "clearhour" / "b2_offsets.json"
LOCAL_B2 = ROOT / "data" / "processed" / "b2_offsets.json"
MODEL_CACHE = ROOT / "data" / "processed" / "model_cache"
FEATURES = [
    "cams_pm2_5", "cams_pm10", "cams_carbon_monoxide", "cams_nitrogen_dioxide", "cams_ozone", "cams_sulphur_dioxide",
    "cams_pm2_5_m3h", "cams_pm2_5_m1h", "cams_pm2_5_p1h", "cams_pm2_5_p3h", "cams_pm2_5_roll24", "cams_pm2_5_dayrank",
    "wx_temperature_2m", "wx_relative_humidity_2m", "wx_wind_speed_10m", "wx_pressure_msl", "wx_precipitation",
    "wx_boundary_layer_height", "wx_wind_dir_sin", "wx_wind_dir_cos",
    "hour", "dow", "month", "doy_sin", "doy_cos", "is_weekend",
]


class ForecastError(RuntimeError):
    """A problem the user can act on; the CLI prints it without a traceback."""


class NetworkError(ForecastError):
    pass


class ForecastWindowError(ForecastError):
    pass


class MissingKeyError(ForecastError):
    pass


# ---------------------------------------------------------------- time
def today_local() -> str:
    return (datetime.now(timezone.utc) + LOCAL_OFFSET).strftime("%Y-%m-%d")


# ---------------------------------------------------------------- live inputs
def fetch(url: str, variables: list[str], past: int = 3, ahead: int = MAX_AHEAD_DAYS) -> pd.DataFrame:
    try:
        r = requests.get(url, params={"latitude": ds.aq_probe.LAT, "longitude": ds.aq_probe.LON, "hourly": ",".join(variables),
                                      "timezone": "Asia/Karachi", "past_days": past, "forecast_days": ahead},
                         headers=UA, timeout=60)
    except requests.RequestException as e:
        host = url.split("/")[2]
        raise NetworkError(f"Cannot reach {host} ({type(e).__name__}). Check your internet connection and try again.") from e
    if not r.ok:
        reason = ""
        try:
            reason = r.json().get("reason", "")
        except ValueError:
            pass
        raise NetworkError(f"{url.split('/')[2]} returned HTTP {r.status_code}. {reason}".strip())
    df = pd.DataFrame(r.json()["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    return df.set_index("time")


def live_features(day: str, past: int = 3, ahead: int = MAX_AHEAD_DAYS) -> tuple[pd.DataFrame, dict]:
    """The 26 features for the 24 local hours of `day` from the live forecast endpoints."""
    cams = fetch(AQ, ds.CAMS_VARS, past, ahead)
    wx = fetch(WX, ds.WX_VARS, past, ahead)
    valid = cams["pm2_5"].dropna()
    meta = {"cams_span": [str(cams.index.min()), str(cams.index.max())], "wx_span": [str(wx.index.min()), str(wx.index.max())],
            "cams_pm2_5_last_valid_hour": str(valid.index.max()), "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
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
    missing_cols = [f for f in FEATURES if f not in df.columns]
    if missing_cols:
        raise ForecastError(f"Open-Meteo response is missing expected variables: {missing_cols}")
    df = df[FEATURES]
    if len(df) < 24 or df.isna().any().any():
        raise ForecastWindowError(
            f"Open-Meteo does not yet have a complete air-quality forecast for {day}. "
            f"The latest hour with data is {valid.index.max():%Y-%m-%d %H:00} (local); "
            f"try a date up to {(valid.index.max() - pd.Timedelta(hours=3)).strftime('%Y-%m-%d')}.")
    return df, meta


def save_matrix(live: pd.DataFrame, day: str, outdir: Path, fetched_utc: str) -> dict:
    """Write the exact 24x26 feature matrix to a CSV (LF endings, name carries the fetch time) and return its path and sha256."""
    outdir.mkdir(parents=True, exist_ok=True)
    stamp = fetched_utc.replace("-", "").replace(":", "").replace("+0000", "Z").replace("+00:00", "Z")
    path = outdir / f"forecast_inputs_{day}_{stamp}.csv"
    live[FEATURES].to_csv(path, index_label="time", lineterminator="\n")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        rel = str(path)
    return {"path": rel, "sha256": sha, "rows": int(len(live)), "columns": len(FEATURES)}


# ---------------------------------------------------------------- training data and models
def training_table(day: str) -> pd.DataFrame:
    """Sensor-derived training rows strictly before `day` (needs OPENAQ_API_KEY)."""
    if not os.environ.get("OPENAQ_API_KEY"):
        raise MissingKeyError("OPENAQ_API_KEY is not set. Training data comes from OpenAQ (free key: https://explore.openaq.org/register). "
                              "Put it in .env as OPENAQ_API_KEY=... (see .env.example).")
    try:
        train = ds.build()
    except requests.RequestException as e:
        raise NetworkError(f"Cannot reach OpenAQ / Open-Meteo to build the training table ({type(e).__name__}).") from e
    train = train[train.index < pd.Timestamp(day)]
    if train.empty:
        raise ForecastError("Training table came back empty (check the OpenAQ key and sensor 4554236).")
    missing = set(FEATURES) - set(train.columns)
    if missing:
        raise ForecastError(f"Training table is missing features: {sorted(missing)}")
    return train


def fit_b2(train: pd.DataFrame) -> dict:
    resid = train["y"] - train["cams_pm2_5"]
    hb = resid.groupby(train.index.hour).mean()
    gm = float(resid.mean())
    return {"hour_offsets": [float(hb.get(h, gm)) for h in range(24)], "global_mean": gm, "n_rows": int(len(train)),
            "first_hour": str(train.index.min()), "last_hour": str(train.index.max()), "sensor_location_id": ds.SENSOR_LOCATION,
            "note": "B2 = raw CAMS pm2_5 + mean(monitor - CAMS) by local hour of day; fitted on sensor-derived hourly rows"}


def load_b2() -> tuple[dict, str]:
    for path, label in ((LOCAL_B2, "local refit"), (PACKAGED_B2, "packaged")):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8")), label
    raise ForecastError("No B2 hour-bias offsets found (src/clearhour/b2_offsets.json is missing). Run `python -m clearhour --refit` with OPENAQ_API_KEY set.")


def predict_b2(live: pd.DataFrame, b2: dict) -> pd.Series:
    off = np.array(b2["hour_offsets"])
    return pd.Series(live["cams_pm2_5"].to_numpy() + off[live.index.hour.to_numpy()], index=live.index)


def tabpfn_key(tr: pd.DataFrame) -> str:
    from importlib.metadata import version
    h = hashlib.sha256()
    h.update(f"tabpfn={version('tabpfn')}|v2-regressor|rows={len(tr)}|{tr.index.min()}|{tr.index.max()}".encode())
    h.update("|".join(FEATURES).encode())
    h.update(pd.util.hash_pandas_object(tr[FEATURES + ["y"]], index=True).to_numpy().tobytes())
    return h.hexdigest()[:20]


def predict_tabpfn(train: pd.DataFrame, live: pd.DataFrame, rows: int = TABPFN_ROWS, use_cache: bool = True,
                   log=lambda s: None) -> tuple[pd.Series, dict]:
    """TabPFN v2 (local CPU, no tuning) fitted on the most recent `rows` training rows; fitted model cached on disk."""
    from tabpfn import TabPFNRegressor
    from tabpfn.constants import ModelVersion
    try:
        from tabpfn.errors import TabPFNLicenseError
    except ImportError:  # pragma: no cover
        TabPFNLicenseError = ()  # type: ignore[assignment]
    tr = train.iloc[-rows:]
    key = tabpfn_key(tr)
    path = MODEL_CACHE / f"tabpfn_v2_{key}.tabpfn_fit"
    t0 = time.time()
    m, cached = None, False
    try:
        if use_cache and path.exists():
            from tabpfn.model_loading import load_fitted_tabpfn_model
            log(f"loading cached fitted model {path.name}")
            m, cached = load_fitted_tabpfn_model(path, device="cpu"), True
        if m is None:
            log(f"fitting TabPFN v2 on {len(tr)} rows (this is the slow step) ...")
            m = TabPFNRegressor.create_default_for_version(ModelVersion.V2, device="cpu", fit_mode="fit_with_cache",
                                                           ignore_pretraining_limits=True, random_state=0)
            m.fit(tr[FEATURES], tr["y"].to_numpy())
            if use_cache:
                try:
                    from tabpfn.model_loading import save_fitted_tabpfn_model
                    MODEL_CACHE.mkdir(parents=True, exist_ok=True)
                    for old in MODEL_CACHE.glob("tabpfn_v2_*.tabpfn_fit"):
                        old.unlink()  # keep only the newest fitted model
                    save_fitted_tabpfn_model(m, path)
                except Exception as e:  # caching is best-effort
                    log(f"(could not cache the fitted model: {type(e).__name__}: {e})")
        pred = pd.Series(m.predict(live[FEATURES]), index=live.index)
    except TabPFNLicenseError as e:
        raise ForecastError("TabPFN needs a one-time licence acceptance or a token to download its weights. "
                            "Accept the licence at https://ux.priorlabs.ai, then set TABPFN_TOKEN in .env. "
                            f"Details: {str(e).splitlines()[0]}") from e
    except (OSError, requests.RequestException) as e:
        if cached:
            raise
        raise NetworkError(f"Could not download or load the TabPFN v2 weights ({type(e).__name__}: {e}). Check your connection.") from e
    info = {"model_path": Path(str(m.model_path)).name, "train_rows": int(len(tr)), "train_first": str(tr.index.min()),
            "train_last": str(tr.index.max()), "seconds": round(time.time() - t0), "cached": cached, "cache_key": key}
    return pred, info


# ---------------------------------------------------------------- shared result assembly
def windows(pred: pd.Series) -> dict:
    w = (pred + pred.shift(-1)).div(2).dropna()
    lo, hi = w.idxmin(), w.idxmax()
    return {"cleanest": {"start": f"{lo:%H:%M}", "end": f"{lo + pd.Timedelta(hours=2):%H:%M}", "pm25": round(float(w[lo]), 1)},
            "dirtiest": {"start": f"{hi:%H:%M}", "end": f"{hi + pd.Timedelta(hours=2):%H:%M}", "pm25": round(float(w[hi]), 1)}}


def model_entry(s: pd.Series) -> dict:
    return {"hourly": [round(float(x), 1) for x in s], "windows": windows(s)}


def caveats(train_rows: int, train_last: str, tabpfn_rows: int | None, b2_source: str | None = None) -> list[str]:
    out = [
        "Inputs are LIVE forecasts from the Open-Meteo air-quality and weather forecast endpoints (not the archives); "
        "the evaluation used archive inputs, so live skill is expected to be worse.",
        "Ground truth is an uncalibrated low-cost AirGradient sensor (OpenAQ 4554236; CC BY 4.0, The Urban Unit), not a reference monitor.",
        "On the held-out TEST month the exact cleanest-window hit rate (both hours inside the actual cleanest 6) was 37% for TabPFN v2 (30% raw CAMS, 43% B2).",
        f"Feature coverage: all {len(FEATURES)} features built from the forecast endpoints; none substituted from archives.",
        "Known differences vs training: training CAMS/weather were archive values; here CAMS comes from the forecast endpoint "
        "(`cams_pm2_5_roll24` and lags use the 3 past days + forecast of the same endpoint), weather from api.open-meteo.com/v1/forecast "
        "(`boundary_layer_height` is a model forecast; in training it was archive).",
    ]
    if tabpfn_rows is not None:
        out.append(f"Training data: monitor hours up to {train_last} ({train_rows} rows); B2 bias offsets fitted on all of it; TabPFN uses the most recent {tabpfn_rows}.")
    else:
        out.append(f"B2 offsets ({b2_source}) were fitted on {train_rows} hourly sensor readings up to {train_last}.")
    return out


def card(day: str, out: dict) -> str:
    now_utc = datetime.fromisoformat(out["generated_utc"])
    local = now_utc.astimezone(timezone(LOCAL_OFFSET))
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


# ---------------------------------------------------------------- pre-registration runner (used for 2026-10-11)
def main() -> None:
    day = sys.argv[1] if len(sys.argv) > 1 else "2026-10-11"
    stage = sys.argv[2] if len(sys.argv) > 2 else "stage2"
    live, meta = live_features(day)
    train = training_table(day)
    b2 = fit_b2(train)
    idx = live.index
    b0 = live["cams_pm2_5"]
    out = {"day": day, "stage": stage, "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "input_meta": meta, "train_rows": len(train), "train_last_hour": str(train.index.max()), "models": {},
           "caveats": caveats(len(train), str(train.index.max()), TABPFN_ROWS), "feature_nulls": {},
           "inputs_hourly": live[["cams_pm2_5", "wx_temperature_2m", "wx_boundary_layer_height"]].round(2).to_dict("list")}
    out["input_matrix"] = save_matrix(live, day, ROOT / "results" / "inputs", meta["fetched_utc"])
    out["models"]["B0 raw CAMS"] = model_entry(b0)
    out["models"]["B2 CAMS+hour bias"] = model_entry(predict_b2(live, b2))

    def write(stage_name: str) -> None:
        out["stage"] = stage_name
        (ROOT / "results" / f"forecast_{day}.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
        (ROOT / "results" / f"forecast_{day}.md").write_text(card(day, out), encoding="utf-8")
        print(f"wrote forecast_{day}.* stage={stage_name}", flush=True)

    write("stage1 (B0 + B2 only; TabPFN fit in progress)")
    if stage == "stage1":
        return
    p, info = predict_tabpfn(train, live, TABPFN_ROWS, use_cache=False, log=lambda s: print(s, flush=True))
    out["tabpfn"] = info
    out["models"] = {"M1 TabPFN v2": model_entry(p), **out["models"]}
    out["generated_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    write("stage2 (all three models)")


if __name__ == "__main__":
    main()
