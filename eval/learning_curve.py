"""Data-efficiency learning curve: how many training hours until each model is usable? (protocol: results/learning_curve.md)

Usage:
  .venv/Scripts/python -m eval.learning_curve run [--budget-min 180] [--dry]   # resumable; cells -> results/learning_curve_cells.json
  .venv/Scripts/python -m eval.learning_curve report                            # md + json from saved cells
Rolling-origin folds, training = N most recent valid rows before each 30-day window, never random subsampling.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eval import evaluate as ev  # noqa: E402

RES = ROOT / "results"
FOLDS = {"F1": "2025-06-13", "F2": "2025-09-18", "F3": "2026-01-04", "F4": "2026-03-23", "F5": "2026-06-12", "F6": "2026-08-11"}
WINDOW_DAYS = 30
PHASES = [("P1", [100, 250, 500, 1000, 2500]), ("P2", [5000]), ("P3", [10000])]
ALL_N = [100, 250, 500, 1000, 2500, 5000, 10000]
MODELS = ["B2 CAMS+hour bias", "B4 Ridge", "B5 HistGBR", "M1 TabPFN v2"]
ALL_MODELS = ["B0 raw CAMS"] + MODELS
XS_N = 2500
SENSOR_B = 4565419
CELLS = RES / "learning_curve_cells.json"


# ------------------------------------------------------------------ helpers
def window(df: pd.DataFrame, start: str) -> pd.DataFrame:
    s = pd.Timestamp(start)
    return df[(df.index >= s) & (df.index < s + pd.Timedelta(days=WINDOW_DAYS))]


def load_cells(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_cells(path: Path, cells: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(cells, indent=1), encoding="utf-8")
    tmp.replace(path)


def predict_all(name: str, train: pd.DataFrame, target: pd.DataFrame, feats: list[str]) -> tuple[np.ndarray, float, float]:
    """Fit `name` on train, predict target. Returns (pred, fit_s, predict_s)."""
    t0 = time.time()
    if name == "B2 CAMS+hour bias":
        resid = train["y"] - train["cams_pm2_5"]
        hb = resid.groupby(train.index.hour).mean()
        gm = float(resid.mean())
        fit_s = time.time() - t0
        t1 = time.time()
        pred = target["cams_pm2_5"].to_numpy() + target.index.hour.map(hb).fillna(gm).to_numpy()
        return pred, fit_s, time.time() - t1
    if name in ("B4 Ridge", "B5 HistGBR"):
        m = (make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=1.0)) if name == "B4 Ridge"
             else HistGradientBoostingRegressor(random_state=0))
        m.fit(train[feats], train["y"].to_numpy())
        fit_s = time.time() - t0
        t1 = time.time()
        return m.predict(target[feats]), fit_s, time.time() - t1
    if name == "M1 TabPFN v2":
        from tabpfn import TabPFNRegressor
        from tabpfn.constants import ModelVersion
        m = TabPFNRegressor.create_default_for_version(ModelVersion.V2, device="cpu", fit_mode="fit_with_cache",
                                                       ignore_pretraining_limits=True, random_state=0)
        m.fit(train[feats], train["y"].to_numpy())
        fit_s = time.time() - t0
        t1 = time.time()
        return m.predict(target[feats]), fit_s, time.time() - t1
    raise ValueError(name)


def cell_record(target: pd.DataFrame, pred: np.ndarray, fit_s: float, pred_s: float, n_train: int, train: pd.DataFrame) -> dict:
    m = ev.metrics(target, pred)
    return {"MAE": m["MAE"], "RMSE": m["RMSE"], "Bias": m["Bias"], "rho_median": m["rho_median"], "rho_mean": m["rho_mean"],
            "n_days": m["n_days"], "hit_pct": m["hit_pct"], "fit_s": round(fit_s, 2), "predict_s": round(pred_s, 2),
            "n_train": n_train, "n_eval": len(target),
            "train_span": [str(train.index.min()), str(train.index.max())] if len(train) else None}


# ------------------------------------------------------------------ run
class Budget:
    def __init__(self, minutes: float):
        self.t0 = time.time()
        self.end = self.t0 + minutes * 60
        self.tabpfn_points: list[tuple[int, float]] = []  # (N, total seconds) of completed TabPFN cells

    def left(self) -> float:
        return self.end - time.time()

    def can_start_tabpfn(self, n: int) -> tuple[bool, float]:
        # Estimate from the nearest completed TabPFN size (exact if the same N was already done), quadratic extrapolation upward.
        same = [s for m, s in self.tabpfn_points if m == n]
        below = [(m, s) for m, s in self.tabpfn_points if m < n]
        if same:
            est = max(same)
        elif below:
            m, s = max(below)
            est = s * (n / m) ** 2
        else:
            est = 0.0
        return self.left() > est * 1.15 + 60, est


def run(budget_min: float, dry: bool) -> None:
    cells_path = RES / ("learning_curve_cells_dry.json" if dry else "learning_curve_cells.json")
    cells = load_cells(cells_path)
    df, feats = ev.load()
    bud = Budget(budget_min)
    for k, v in cells.items():  # resume: seed the time estimator with TabPFN cells finished in earlier sessions
        if k.endswith("M1 TabPFN v2") and "fit_s" in v and not k.startswith("XS"):
            bud.tabpfn_points.append((int(k.split("|")[1]), v["fit_s"] + v["predict_s"]))
    log = lambda s: print(f"[{(time.time() - bud.t0) / 60:6.1f} min] {s}", flush=True)  # noqa: E731
    models = [m for m in MODELS if not (dry and m.startswith("M1"))]

    def one(key_prefix: str, train: pd.DataFrame, target: pd.DataFrame, n: int, tgt_feats: list[str], model_list: list[str], tag: str) -> bool:
        for name in model_list:
            key = f"{key_prefix}|{name}"
            if key in cells:
                continue
            if name.startswith("M1"):
                ok, est = bud.can_start_tabpfn(n)
                if not ok:
                    log(f"SKIP (budget) {key}: est {est / 60:.0f} min, {bud.left() / 60:.0f} min left")
                    cells[key] = {"not_run": "budget", "est_s": round(est)}
                    save_cells(cells_path, cells)
                    continue
            pred, fit_s, pred_s = predict_all(name, train, target, tgt_feats)
            cells[key] = cell_record(target, pred, fit_s, pred_s, len(train), train)
            if name.startswith("M1"):
                bud.tabpfn_points.append((n, fit_s + pred_s))
            save_cells(cells_path, cells)
            c = cells[key]
            log(f"{tag} {name:18s} N={n:5d}  MAE {c['MAE']:5.1f}  rho {c['rho_median']:.3f}  hit {c['hit_pct']:3.0f}%  fit {c['fit_s']:.0f}s pred {c['predict_s']:.0f}s")
        return True

    # B0 reference per fold
    for f, start in FOLDS.items():
        key = f"{f}|ref|B0 raw CAMS"
        if key not in cells:
            tgt = window(df, start)
            cells[key] = cell_record(tgt, tgt["cams_pm2_5"].to_numpy(), 0.0, 0.0, 0, tgt.iloc[:0])
            save_cells(cells_path, cells)
    for phase, ns in PHASES:
        for n in ns:
            for f, start in FOLDS.items():
                before = df[df.index < pd.Timestamp(start)]
                tgt = window(df, start)
                prefix = f"{f}|{n}"
                if len(before) < n:
                    cells.setdefault(f"{prefix}|_skip", {"skipped": "insufficient history", "rows_before": len(before)})
                    save_cells(cells_path, cells)
                    continue
                one(prefix, before.iloc[-n:], tgt, n, feats, models, f"{phase} {f}")
            log(f"-- finished N={n} across folds; {bud.left() / 60:.0f} min left")
    # Phase 4: cross-sensor transfer (only with time to spare)
    if dry:
        return
    if bud.left() < 15 * 60:
        log("Phase 4 skipped: <15 min left")
        return
    sys.path.insert(0, str(ROOT))
    from datetime import date as _d
    from src import dataset as ds
    pb = ROOT / "data" / "processed" / f"hourly_{SENSOR_B}.parquet"
    if not pb.exists():
        ds.SENSOR_LOCATION, ds.START = SENSOR_B, _d(2025, 5, 30)
        b = ds.build()
        b.to_parquet(pb)
    dfb = pd.read_parquet(pb)
    dfb["day"] = dfb.index.normalize()
    log(f"Phase 4: sensor {SENSOR_B}, {len(dfb)} rows")
    for kind in ("transfer", "native"):  # transfer first; native reference only if time remains
        for f, start in FOLDS.items():
            before_a = df[df.index < pd.Timestamp(start)]
            before_b = dfb[dfb.index < pd.Timestamp(start)]
            tgt_b = window(dfb, start)
            train = before_a if kind == "transfer" else before_b
            if len(train) < XS_N or len(tgt_b) < 100:
                continue
            if bud.left() < 6 * 60:
                log("Phase 4 stopping: budget")
                return
            one(f"XS|{kind}|{f}|{XS_N}", train.iloc[-XS_N:], tgt_b, XS_N, feats, models, f"P4 {kind} {f}")
            for name_ref in ("B0 raw CAMS",):
                key = f"XS|{kind}|{f}|{XS_N}|{name_ref}"
                if key not in cells:
                    cells[key] = cell_record(tgt_b, tgt_b["cams_pm2_5"].to_numpy(), 0.0, 0.0, 0, tgt_b.iloc[:0])
                    save_cells(cells_path, cells)
    log("done")


# ------------------------------------------------------------------ report
def agg(vals: list[float]) -> dict:
    a = np.array(vals, dtype=float)
    return {"n": int(len(a)), "mean": float(a.mean()), "std": float(a.std(ddof=1)) if len(a) > 1 else None}


def fmt(a: dict, d: int = 1) -> str:
    if a["n"] == 0:
        return "—"
    return f"{a['mean']:.{d}f} ± {a['std']:.{d}f}" if a["std"] is not None else f"{a['mean']:.{d}f} (1 fold)"


def done(cells: dict, f: str, n: int, model: str) -> dict | None:
    c = cells.get(f"{f}|{n}|{model}")
    return c if c and "MAE" in c else None


def report() -> None:
    cells = load_cells(CELLS)
    folds = list(FOLDS)
    ref = {f: cells[f"{f}|ref|B0 raw CAMS"] for f in folds if f"{f}|ref|B0 raw CAMS" in cells}
    present = {n: [f for f in folds if all(done(cells, f, n, m) for m in MODELS[:3])] for n in ALL_N}
    curves: dict = {}
    for n in ALL_N:
        for m in ALL_MODELS:
            fs = [f for f in folds if (m.startswith("B0") and f in ref and f in present[n]) or (not m.startswith("B0") and done(cells, f, n, m))]
            if not fs:
                continue
            get = (lambda f, k: ref[f][k]) if m.startswith("B0") else (lambda f, k, m=m, n=n: done(cells, f, n, m)[k])
            curves.setdefault(m, {})[n] = {"folds": fs, **{k: agg([get(f, k) for f in fs]) for k in ("MAE", "RMSE", "rho_median", "hit_pct")}}
    skipped = {n: [f for f in folds if f"{f}|{n}|_skip" in cells] for n in ALL_N}
    notrun = [(f, n, m) for n in ALL_N for f in folds for m in MODELS
              if f"{f}|{n}|{m}" in cells and "not_run" in cells[f"{f}|{n}|{m}"]]
    missing = [(f, n, m) for n in ALL_N for f in folds if f not in skipped[n] for m in MODELS if not done(cells, f, n, m)]

    protocol = (RES / "learning_curve.md").read_text(encoding="utf-8").split("<!-- RESULTS BELOW -->")[0]
    L = [protocol.rstrip(), "", "<!-- RESULTS BELOW -->", "", "# Results", "", f"Generated {pd.Timestamp.now():%Y-%m-%d %H:%M} local by `eval/learning_curve.py report`.", ""]

    def table(metric: str, title: str, d: int) -> None:
        L.extend([f"### {title} (mean ± std over folds; n folds in brackets)", "",
                  "| N | " + " | ".join(ALL_MODELS) + " |", "|---|" + "---|" * len(ALL_MODELS)])
        for n in ALL_N:
            if not any(n in curves.get(m, {}) for m in ALL_MODELS):
                continue
            row = [f"{fmt(curves[m][n][metric], d)} [{curves[m][n]['MAE']['n']}]" if n in curves.get(m, {}) else "—" for m in ALL_MODELS]
            L.append(f"| {n} | " + " | ".join(row) + " |")
        L.append("")

    table("MAE", "MAE (µg/m³)", 1)
    table("RMSE", "RMSE (µg/m³)", 1)
    table("rho_median", "Median within-day Spearman ρ (per-fold median, then averaged)", 3)
    table("hit_pct", "Top-2h-window hit % (exact cleanest 2h inside actual cleanest 6h)", 0)

    # per-fold pivots
    for metric, title, d in (("MAE", "MAE", 1), ("rho_median", "median ρ", 3), ("hit_pct", "hit %", 0)):
        L.extend([f"### Per-fold {title}", "", "| N | Model | " + " | ".join(folds) + " |", "|---|---|" + "---|" * len(folds)])
        for n in ALL_N:
            for m in MODELS:
                vals = [done(cells, f, n, m) for f in folds]
                if any(vals):
                    L.append(f"| {n} | {m} | " + " | ".join(f"{v[metric]:.{d}f}" if v else ("skip" if f in skipped[n] else "·") for v, f in zip(vals, folds)) + " |")
        L.append("| ref | B0 raw CAMS | " + " | ".join(f"{ref[f][metric]:.{d}f}" if f in ref else "·" for f in folds) + " |")
        L.append("")
    L.append("Legend: `skip` = fewer than N valid rows before the window; `·` = not run / not completed.\n")

    # paired differences
    L.extend(["### Paired per-fold differences (TabPFN − other; negative MAE diff / positive ρ diff = TabPFN better)", "",
              "| N | vs | folds | mean ΔMAE | TabPFN better on MAE | mean Δρ | TabPFN better on ρ |", "|---|---|---|---|---|---|---|"])
    verdict: dict[int, dict] = {}
    for n in ALL_N:
        res = {}
        for other in ("B2 CAMS+hour bias", "B4 Ridge", "B5 HistGBR"):
            fs = [f for f in folds if done(cells, f, n, "M1 TabPFN v2") and done(cells, f, n, other)]
            if not fs:
                continue
            dm = [done(cells, f, n, "M1 TabPFN v2")["MAE"] - done(cells, f, n, other)["MAE"] for f in fs]
            dr = [done(cells, f, n, "M1 TabPFN v2")["rho_median"] - done(cells, f, n, other)["rho_median"] for f in fs]
            res[other] = {"folds": len(fs), "mae_better": sum(x < 0 for x in dm), "rho_better": sum(x > 0 for x in dr)}
            L.append(f"| {n} | {other} | {len(fs)} | {np.mean(dm):+.2f} | {res[other]['mae_better']}/{len(fs)} | {np.mean(dr):+.3f} | {res[other]['rho_better']}/{len(fs)} |")
        if res:
            nf = max(v["folds"] for v in res.values())
            verdict[n] = {"nf": nf, "wins_mae": all(v["mae_better"] > v["folds"] / 2 for v in res.values()) and len(res) == 3,
                          "wins_rho": all(v["rho_better"] > v["folds"] / 2 for v in res.values()) and len(res) == 3}
    L.append("")

    # rule-based verdict + usable
    L.extend(["### Pre-declared rules applied", "", "| N | folds | TabPFN wins on MAE (majority of folds vs every other trained model)? | TabPFN wins on ρ? |", "|---|---|---|---|"])
    for n, v in verdict.items():
        L.append(f"| {n} | {v['nf']} | {'YES' if v['wins_mae'] else 'no'} | {'YES' if v['wins_rho'] else 'no'} |")
    L.extend(["", "Usable = mean MAE (over the folds available at N) below B0 raw CAMS's mean MAE over the same folds:", "",
              "| Model | " + " | ".join(str(n) for n in ALL_N) + " |", "|---|" + "---|" * len(ALL_N)])
    usable_first = {}
    for m in MODELS:
        row = []
        for n in ALL_N:
            if n in curves.get(m, {}) and n in curves.get("B0 raw CAMS", {}):
                ok = curves[m][n]["MAE"]["mean"] < curves["B0 raw CAMS"][n]["MAE"]["mean"]
                row.append("yes" if ok else "no")
                if ok and m not in usable_first:
                    usable_first[m] = n
            else:
                row.append("·")
        L.append(f"| {m} | " + " | ".join(row) + " |")
    L.extend(["", "Smallest N at which each model is usable: " + "; ".join(f"{m}: {usable_first.get(m, 'never in tested range')}" for m in MODELS), ""])

    # fit time
    L.extend(["### Wall-clock time per (model, N), mean over folds (seconds: fit / predict on ~700 eval rows)", "",
              "| N | " + " | ".join(MODELS) + " |", "|---|" + "---|" * len(MODELS)])
    ft: dict = {}
    for n in ALL_N:
        row = []
        for m in MODELS:
            cs = [done(cells, f, n, m) for f in folds if done(cells, f, n, m)]
            if cs:
                ft.setdefault(m, {})[n] = {"fit_s": float(np.mean([c["fit_s"] for c in cs])), "predict_s": float(np.mean([c["predict_s"] for c in cs])), "n": len(cs)}
                row.append(f"{ft[m][n]['fit_s']:.1f} / {ft[m][n]['predict_s']:.1f}")
            else:
                row.append("—")
        if any(r != "—" for r in row):
            L.append(f"| {n} | " + " | ".join(row) + " |")
    L.append("")

    # missing
    L.extend(["### Skipped and missing cells", ""])
    for n in ALL_N:
        if skipped[n]:
            L.append(f"- N={n}: skipped (insufficient history before window) in {', '.join(skipped[n])}")
    if notrun:
        L.append("- Not run (time budget): " + ", ".join(f"{f}/N={n}/{m}" for f, n, m in notrun))
    other_missing = [x for x in missing if x not in notrun]
    L.append("- Missing for other reasons: " + (", ".join(f"{f}/N={n}/{m}" for f, n, m in other_missing) if other_missing else "none"))
    L.append("")

    # cross-sensor
    xs = {k: v for k, v in cells.items() if k.startswith("XS|") and "MAE" in v}
    xs_out: dict = {}
    if xs:
        L.extend([f"### Cross-sensor transfer: train at sensor 4554236 (N={XS_N}), evaluate at sensor {SENSOR_B}, no retraining", ""])
        for kind, title in (("transfer", "Transfer (trained on 4554236)"), ("native", f"Native reference (trained on {SENSOR_B}'s own preceding rows)")):
            fs = [f for f in folds if any(k.startswith(f"XS|{kind}|{f}|") for k in xs)]
            if not fs:
                continue
            L.extend([f"**{title}**, folds {', '.join(fs)}", "", "| Model | MAE | RMSE | median ρ | hit % |", "|---|---|---|---|---|"])
            for m in ALL_MODELS:
                got = [xs[f"XS|{kind}|{f}|{XS_N}|{m}"] for f in fs if f"XS|{kind}|{f}|{XS_N}|{m}" in xs]
                if got:
                    a = {k: agg([g[k] for g in got]) for k in ("MAE", "RMSE", "rho_median", "hit_pct")}
                    xs_out.setdefault(kind, {})[m] = {"folds": len(got), **a}
                    L.append(f"| {m} | {fmt(a['MAE'])} | {fmt(a['RMSE'])} | {fmt(a['rho_median'], 3)} | {fmt(a['hit_pct'], 0)} |")
            L.append("")

    reading = RES / "learning_curve_reading.md"
    if reading.exists():
        L.extend(["<!-- READING -->", "", reading.read_text(encoding="utf-8").rstrip(), ""])
    (RES / "learning_curve.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    out = {"question": "data efficiency: usable after how many hours?", "folds": {f: {"window_start": s, "days": WINDOW_DAYS} for f, s in FOLDS.items()},
           "n_values": ALL_N, "curves": curves, "fit_time": ft, "paired_verdict": {str(k): v for k, v in verdict.items()},
           "usable_first_n": usable_first, "skipped": {str(k): v for k, v in skipped.items()},
           "missing": [list(x) for x in missing], "cross_sensor": xs_out,
           "per_fold_cells": {k: v for k, v in cells.items() if "MAE" in v}}
    (RES / "learning_curve.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("wrote results/learning_curve.md and .json")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "run":
        bm = float(sys.argv[sys.argv.index("--budget-min") + 1]) if "--budget-min" in sys.argv else 180.0
        run(bm, "--dry" in sys.argv)
    else:
        report()
