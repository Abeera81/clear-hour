"""Clear Hour evaluation: baselines vs TabPFN v2 on a strict temporal split.

Usage:
  .venv/Scripts/python -m eval.evaluate dev    # all decisions use this
  .venv/Scripts/python -m eval.evaluate test   # run ONCE, only after DEV results are written
  .venv/Scripts/python -m eval.evaluate report # rebuild results/evaluation.md from saved JSON

DEV: models fit on TRAIN, scored on DEV.
TEST: models refit on TRAIN+DEV (pre-registered before TEST was touched), scored on TEST.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "hourly.parquet"
RES = ROOT / "results"
SPLIT_DAYS = 30
TABPFN_MAX_ROWS = 10_000
MIN_HOURS = 20
N_BOOT = 1000
SEED = 0
MODELS = ["B0 raw CAMS", "B1 CAMS+const bias", "B2 CAMS+hour bias", "B3 CAMS+hour×season bias",
          "B4 Ridge", "B5 HistGBR", "M1 TabPFN v2"]


# ---------------------------------------------------------------- data + split
def load() -> tuple[pd.DataFrame, list[str]]:
    df = pd.read_parquet(DATA)
    df["day"] = df.index.normalize()
    feats = [c for c in df.columns if c not in ("y", "day")]
    return df, feats


def split(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    last = df["day"].max()
    test_start = last - pd.Timedelta(days=SPLIT_DAYS - 1)
    dev_start = test_start - pd.Timedelta(days=SPLIT_DAYS)
    return {"train": df[df["day"] < dev_start],
            "dev": df[(df["day"] >= dev_start) & (df["day"] < test_start)],
            "test": df[df["day"] >= test_start]}


def season(idx: pd.DatetimeIndex) -> np.ndarray:
    return np.where(idx.month.isin([10, 11, 12]), "octdec", "rest")


# ---------------------------------------------------------------- models
def fit_predict(train: pd.DataFrame, target: pd.DataFrame, feats: list[str], log: dict) -> dict[str, np.ndarray]:
    preds = {}
    cams_tr, cams_te = train["cams_pm2_5"].to_numpy(), target["cams_pm2_5"].to_numpy()
    resid = train["y"] - train["cams_pm2_5"]
    preds["B0 raw CAMS"] = cams_te
    preds["B1 CAMS+const bias"] = cams_te + resid.mean()
    hb = resid.groupby(train.index.hour).mean()
    preds["B2 CAMS+hour bias"] = cams_te + target.index.hour.map(hb).fillna(resid.mean()).to_numpy()
    key_tr = pd.MultiIndex.from_arrays([train.index.hour, season(train.index)])
    hsb = resid.groupby(key_tr).mean()
    key_te = list(zip(target.index.hour, season(target.index)))
    fallback = target.index.hour.map(hb).to_numpy()
    preds["B3 CAMS+hour×season bias"] = cams_te + np.array(
        [hsb.get(k, fb) for k, fb in zip(key_te, fallback)], dtype=float)
    log["B3_season_cells_in_train"] = sorted({s for _, s in hsb.index})

    X_tr, X_te, y_tr = train[feats], target[feats], train["y"].to_numpy()
    ridge = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=1.0))
    preds["B4 Ridge"] = ridge.fit(X_tr, y_tr).predict(X_te)
    preds["B5 HistGBR"] = HistGradientBoostingRegressor(random_state=SEED).fit(X_tr, y_tr).predict(X_te)

    from tabpfn import TabPFNRegressor
    from tabpfn.constants import ModelVersion
    tr = train.iloc[-TABPFN_MAX_ROWS:] if len(train) > TABPFN_MAX_ROWS else train
    log["tabpfn_train_rows"] = len(tr)
    log["tabpfn_train_span"] = [str(tr.index.min()), str(tr.index.max())]
    log["tabpfn_subsampled"] = len(train) > TABPFN_MAX_ROWS
    t = time.time()
    m = TabPFNRegressor.create_default_for_version(
        ModelVersion.V2, device="cpu", fit_mode="fit_with_cache",
        ignore_pretraining_limits=True,  # required for >1000 rows on CPU; not a tuning knob
        random_state=SEED)
    m.fit(tr[feats], tr["y"].to_numpy())
    preds["M1 TabPFN v2"] = m.predict(X_te)
    log["tabpfn_seconds"] = round(time.time() - t, 1)
    log["tabpfn_model_path"] = str(m.model_path)
    return preds


# ---------------------------------------------------------------- metrics
def per_day(df: pd.DataFrame, pred: np.ndarray) -> pd.DataFrame:
    d = pd.DataFrame({"y": df["y"].to_numpy(), "p": pred, "day": df["day"].to_numpy()}, index=df.index)
    rows = []
    for day, g in d.groupby("day"):
        if len(g) < MIN_HOURS:
            continue
        rho = g["p"].corr(g["y"], method="spearman")
        # consecutive 2-hour windows where both hours are present
        nxt = g.shift(-1)
        ok = np.append(np.diff(g.index.values) == np.timedelta64(1, "h"), False)
        if not ok.any():
            continue
        wp = ((g["p"] + nxt["p"]) / 2)[ok]
        wy = ((g["y"] + nxt["y"]) / 2)[ok]
        start = wp.idxmin()
        chosen = {start, start + pd.Timedelta(hours=1)}
        clean6 = set(g["y"].nsmallest(6).index)
        rows.append({"day": day, "rho": rho, "hit": chosen <= clean6, "chosen": wy.loc[start],
                     "best": wy.min(), "mean": g["y"].mean()})
    return pd.DataFrame(rows)


def metrics(df: pd.DataFrame, pred: np.ndarray) -> dict:
    err = pred - df["y"].to_numpy()
    pdy = per_day(df, pred)
    return {"MAE": float(np.abs(err).mean()), "RMSE": float(np.sqrt((err ** 2).mean())), "Bias": float(err.mean()),
            "rho_median": float(pdy["rho"].median()), "rho_mean": float(pdy["rho"].mean()), "n_days": int(len(pdy)),
            "hit_pct": float(100 * pdy["hit"].mean()), "win_chosen": float(pdy["chosen"].mean()),
            "win_best": float(pdy["best"].mean()), "day_mean": float(pdy["mean"].mean())}


def bootstrap(df: pd.DataFrame, preds: dict[str, np.ndarray]) -> dict:
    """Day-block bootstrap (resample whole days) for MAE and median within-day Spearman."""
    rng = np.random.default_rng(SEED)
    days = df["day"].unique()
    by_day = {d: np.flatnonzero(df["day"].to_numpy() == d) for d in days}
    pd_tab = {k: per_day(df, preds[k]).set_index("day") for k in ("M1 TabPFN v2", "B2 CAMS+hour bias")}
    y = df["y"].to_numpy()
    stats = {k: {"MAE": [], "rho_median": []} for k in pd_tab}
    diff_mae, diff_rho = [], []
    for _ in range(N_BOOT):
        samp = rng.choice(days, size=len(days), replace=True)
        idx = np.concatenate([by_day[d] for d in samp])
        for k in pd_tab:
            stats[k]["MAE"].append(np.abs(preds[k][idx] - y[idx]).mean())
            rhos = pd_tab[k]["rho"].reindex(samp).dropna()
            stats[k]["rho_median"].append(rhos.median())
        diff_mae.append(stats["M1 TabPFN v2"]["MAE"][-1] - stats["B2 CAMS+hour bias"]["MAE"][-1])
        diff_rho.append(stats["M1 TabPFN v2"]["rho_median"][-1] - stats["B2 CAMS+hour bias"]["rho_median"][-1])
    ci = lambda a: [float(np.nanpercentile(a, 2.5)), float(np.nanpercentile(a, 97.5))]  # noqa: E731
    out = {k: {m: ci(v) for m, v in s.items()} for k, s in stats.items()}
    out["TabPFN − B2"] = {"MAE": ci(diff_mae), "rho_median": ci(diff_rho)}
    return out


# ---------------------------------------------------------------- validity check
def validity() -> dict:
    sys.path.insert(0, str(ROOT / "scripts"))
    import ground_truth_probe as gt

    def series(loc_id: int, start: str, end: str) -> pd.Series:
        loc = gt.get(f"/locations/{loc_id}")["results"][0]
        sid = next(s["id"] for s in loc["sensors"] if s["parameter"]["name"] == "pm25")
        return gt.clean(gt.hours(sid, pd.Timestamp(start).date(), pd.Timestamp(end).date()))

    # StateAir feed (8634) ended 2025-03-04, before the sensor started; only the AirNow feed overlaps.
    emb = series(233470, "2025-05-29", "2026-02-17")
    sen = series(4554236, "2025-05-29", "2026-02-17")
    j = pd.concat({"emb": emb, "sen": sen}, axis=1, join="inner").dropna()
    d = j["sen"] - j["emb"]
    jd = j.resample("D").mean().dropna()
    return {"n": int(len(j)), "span": [str(j.index.min()), str(j.index.max())], "r": float(j["emb"].corr(j["sen"])),
            "r_daily": float(jd["emb"].corr(jd["sen"])), "mean_diff": float(d.mean()), "mae": float(d.abs().mean()),
            "emb_mean": float(j["emb"].mean()), "sen_mean": float(j["sen"].mean()),
            "ratio_median": float((j["sen"] / j["emb"])[j["emb"] > 5].median())}


# ---------------------------------------------------------------- runs
def run(which: str) -> None:
    df, feats = load()
    sp = split(df)
    out_json = RES / f"eval_{which}.json"
    if which == "test":
        if not (RES / "eval_dev.json").exists():
            sys.exit("Refusing: DEV results must be written before TEST is touched.")
        if out_json.exists():
            sys.exit("Refusing: TEST already evaluated once (results/eval_test.json exists).")
        train, target = pd.concat([sp["train"], sp["dev"]]), sp["test"]
    else:
        train, target = sp["train"], sp["dev"]
    log: dict = {}
    preds = fit_predict(train, target, feats, log)
    res = {"which": which, "fit_rows": len(train), "fit_span": [str(train.index.min()), str(train.index.max())],
           "eval_rows": len(target), "eval_span": [str(target.index.min()), str(target.index.max())],
           "log": log, "metrics": {k: metrics(target, preds[k]) for k in MODELS},
           "bootstrap": bootstrap(target, preds)}
    if which == "dev":
        res["split"] = {k: {"rows": len(v), "first": str(v.index.min()), "last": str(v.index.max()),
                            "days": int(v["day"].nunique())} for k, v in sp.items()}
        res["features"] = feats
        res["validity"] = validity()
    out_json.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res["metrics"], indent=1))
    report()


def table(res: dict) -> list[str]:
    out = ["| Model | MAE | RMSE | Bias | Within-day ρ median | ρ mean | Days | Top-2h-window hit % | "
           "Chosen window actual | Best possible window | Day mean |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for k in MODELS:
        m = res["metrics"][k]
        out.append(f"| {k} | {m['MAE']:.1f} | {m['RMSE']:.1f} | {m['Bias']:+.1f} | {m['rho_median']:.3f} | "
                   f"{m['rho_mean']:.3f} | {m['n_days']} | {m['hit_pct']:.0f}% | {m['win_chosen']:.1f} | "
                   f"{m['win_best']:.1f} | {m['day_mean']:.1f} |")
    b = res["bootstrap"]
    out += ["", f"Day-block bootstrap ({N_BOOT} resamples) 95% CI:", "",
            "| | MAE | Median within-day ρ |", "|---|---|---|"]
    for k, v in b.items():
        out.append(f"| {k} | [{v['MAE'][0]:.1f}, {v['MAE'][1]:.1f}] | [{v['rho_median'][0]:.3f}, {v['rho_median'][1]:.3f}] |")
    return out


def verdict(res: dict) -> str:
    m, b2, ci = res["metrics"]["M1 TabPFN v2"], res["metrics"]["B2 CAMS+hour bias"], res["bootstrap"]["TabPFN − B2"]

    def word(lo, hi, better_if_negative):
        if hi < 0:
            return "better than" if better_if_negative else "worse than"
        if lo > 0:
            return "worse than" if better_if_negative else "better than"
        return "not distinguishable from"
    mt = res["metrics"]
    best = {k: (min if k in ("MAE", "RMSE") else max)(MODELS, key=lambda n: mt[n][k] if k != "Bias" else -abs(mt[n][k]))
            for k in ("MAE", "RMSE", "Bias", "rho_median", "hit_pct")}
    best_line = "Best model per metric: " + "; ".join(
        f"{k} → {n}" + (" (|bias| smallest)" if k == "Bias" else "") for k, n in best.items()) + "."
    return (f"**TabPFN vs B2** — MAE {m['MAE']:.1f} vs {b2['MAE']:.1f} (TabPFN−B2 95% CI [{ci['MAE'][0]:.1f}, {ci['MAE'][1]:.1f}] → "
            f"TabPFN is **{word(*ci['MAE'], True)}** B2); median within-day ρ {m['rho_median']:.3f} vs {b2['rho_median']:.3f} "
            f"(CI of difference [{ci['rho_median'][0]:.3f}, {ci['rho_median'][1]:.3f}] → TabPFN is **{word(*ci['rho_median'], False)}** "
            f"B2 on ranking).\n\n{best_line}")


LIMITATIONS = """## Limitations

- **Ground truth is an uncalibrated low-cost sensor** (AirGradient, OpenAQ 4554236). Absolute µg/m³ errors are relative to this sensor, not to a reference monitor; see the validity check.
- **CAMS and weather inputs are archive values, not true day-ahead forecasts.** The Open-Meteo CAMS archive is stitched from the most recent model runs, and the weather archive is reanalysis/best-match. A real day-ahead run uses older forecasts (lead 24–48 h), so live skill will likely be worse than shown here for all CAMS-based models alike.
- **Short history**: the sensor starts 2025-05-29, so TRAIN contains exactly one Oct–Dec smog season (2025). B3's season cells and any seasonal learning rest on that single season.
- **DEV/TEST are 30 days each** (late Aug → early Oct 2026), i.e. the transition into smog season; they say little about mid-winter performance. Bootstrap CIs are by day and so reflect only ~30 independent days.
- **TabPFN context limit**: TabPFN sees at most the most recent 10,000 training rows; older rows are dropped for it (not for the other models).
- **Single location, single sensor**: one AirGradient unit can drift, be moved, or be locally affected; no cross-sensor consistency check is done here.
- CAMS alignment (instantaneous value at hour start vs the monitor's hourly mean) is a fixed convention; ±1 h CAMS shifts are provided as features so learned models can adjust, the bias baselines cannot.
"""


def report() -> None:
    dev = json.loads((RES / "eval_dev.json").read_text(encoding="utf-8"))
    tp = RES / "eval_test.json"
    test = json.loads(tp.read_text(encoding="utf-8")) if tp.exists() else None
    md = ["# Clear Hour — dataset + TabPFN evaluation", "",
          "Task: correct the CAMS forecast to predict hourly PM2.5 at OpenAQ sensor 4554236 (Rawalpindi Women University, "
          "AirGradient **uncalibrated low-cost sensor**, 5.2 km from the CAMS point; CC BY 4.0, attribution: The Urban Unit), "
          "then rank the hours of each day. Generated by `eval/evaluate.py` from `data/processed/hourly.parquet` "
          "(built by `src/dataset.py`).", "",
          "## Dataset", "",
          f"- One row per local hour (Asia/Karachi) with a valid monitor reading; `time` = hour start, y = monitor hourly mean.",
          f"- Rows: **{sum(v['rows'] for v in dev['split'].values())}**. CAMS artifact days 2022-12-14/15 excluded (outside sensor span anyway).",
          f"- Features ({len(dev['features'])}, all forecast-available; no monitor reading is a feature): " + ", ".join(f"`{f}`" for f in dev["features"]), "",
          "## Split (strictly temporal, no shuffling)", "", "| Split | First hour | Last hour | Days | Rows |", "|---|---|---|---|---|"]
    for k in ("train", "dev", "test"):
        s = dev["split"][k]
        md.append(f"| {k.upper()} | {s['first']} | {s['last']} | {s['days']} | {s['rows']} |")
    lg = dev["log"]
    md += ["", f"- TabPFN training rows for DEV: **{lg['tabpfn_train_rows']}** "
           + (f"(TRAIN exceeds {TABPFN_MAX_ROWS}: subsampled to the most recent {TABPFN_MAX_ROWS} rows, "
              f"{lg['tabpfn_train_span'][0]} → {lg['tabpfn_train_span'][1]})" if lg["tabpfn_subsampled"] else "(no subsampling needed)"),
           f"- TabPFN: `{Path(lg['tabpfn_model_path']).name}`, TabPFNRegressor v2, fit_mode=fit_with_cache, CPU, "
           f"`ignore_pretraining_limits=True` (required by tabpfn for >1,000 rows on CPU), no tuning; fit+predict {lg['tabpfn_seconds']} s.",
           "- Pre-registered before TEST: for TEST, every model is refit on TRAIN+DEV (TabPFN: most recent 10,000 rows of that) and scored once on TEST.",
           "", "Metric definitions: Bias = mean(pred − actual). Within-day ρ = Spearman(pred, actual) per day with ≥20 hours. "
           "Top-2h-window hit = model's lowest-predicted 2 consecutive hours both fall in the day's 6 lowest actual hours. "
           "Window columns = mean actual PM2.5 (µg/m³) of the model's chosen window / the best possible 2-h window / the day mean, averaged over days.",
           "", f"## DEV results (fit TRAIN, score DEV: {dev['eval_span'][0]} → {dev['eval_span'][1]}, {dev['eval_rows']} rows)", ""]
    md += table(dev) + ["", verdict(dev), ""]
    df, _ = load()
    sp = split(df)
    r = {k: float((v["y"] - v["cams_pm2_5"]).mean()) for k, v in sp.items() if k != "test" or test}
    md += [f"Residual context (mean of monitor − CAMS): TRAIN {r['train']:+.1f}, DEV {r['dev']:+.1f}"
           + (f", TEST {r['test']:+.1f}" if test else "") + " µg/m³. "
           "The bias baselines (B1–B3) learn TRAIN's offset, which is dominated by winter, when the sensor reads far above CAMS.", ""]
    md += ["## TEST results (held out, evaluated once)", ""]
    if test:
        md += [f"Fit TRAIN+DEV ({test['fit_rows']} rows; TabPFN {test['log']['tabpfn_train_rows']}), score TEST "
               f"{test['eval_span'][0]} → {test['eval_span'][1]}, {test['eval_rows']} rows.", ""]
        md += table(test) + ["", verdict(test), ""]
    else:
        md += ["_Not yet run._", ""]
    v = dev["validity"]
    trust = ("tracks the reference monitor's day-to-day changes well" if v["r_daily"] >= 0.8 else
             "tracks the reference monitor only moderately")
    md += ["## Validity check — sensor 4554236 vs US Embassy reference monitor", "",
           f"- Overlap: **{v['n']} h** ({v['span'][0][:10]} → {v['span'][1][:10]}), ~15 km apart",
           f"- Hourly Pearson r **{v['r']:.3f}**; daily-mean r **{v['r_daily']:.3f}**",
           f"- Mean difference (sensor − embassy) **{v['mean_diff']:+.1f} µg/m³**; MAE **{v['mae']:.1f}**; "
           f"means {v['sen_mean']:.1f} (sensor) vs {v['emb_mean']:.1f} (embassy); median ratio sensor/embassy {v['ratio_median']:.2f}", "",
           f"The low-cost sensor {trust} (daily r {v['r_daily']:.2f}, hourly r {v['r']:.2f}) but differs in level "
           f"(mean difference {v['mean_diff']:+.1f} µg/m³) and is 15 km away in a different part of the city, so hourly disagreement mixes "
           "sensor error with real spatial differences. We therefore treat its absolute values as indicative only and lean on the "
           "ranking metrics (which ignore level offsets) as the product metric.", "",
           LIMITATIONS]
    (RES / "evaluation.md").write_text("\n".join(md), encoding="utf-8")
    print(f"wrote results/evaluation.md")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "dev"
    report() if arg == "report" else run(arg)
