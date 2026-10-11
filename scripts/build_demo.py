"""Build docs/index.html: one self-contained static demo page (inline CSS/JS, no external requests).

Usage: .venv/Scripts/python scripts/build_demo.py [YYYY-MM-DD] [--actuals PATH]

Inputs: results/forecast_<day>.json, results/learning_curve.json, results/eval_test.json,
        results/actuals_<day>.json (OPTIONAL; if it does not exist the page shows "Pending" - nothing is guessed).
The page draws its charts client-side from embedded data, so they fit any width (checked at 390 px and 1280 px).
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from score_forecast import best_pair, default_from_hour  # noqa: E402

REPO = "https://github.com/Abeera81/field-window"
LC_N = [100, 250, 500, 1000, 2500, 5000]
MODEL_KEY = {"M1 TabPFN v2": "tabpfn", "B2 CAMS+hour bias": "b2", "B0 raw CAMS": "b0", "B5 HistGBR": "hgb", "B4 Ridge": "ridge"}
LABEL = {"M1 TabPFN v2": "TabPFN v2", "B2 CAMS+hour bias": "B2 hour-bias", "B0 raw CAMS": "B0 raw CAMS", "B5 HistGBR": "HistGBR", "B4 Ridge": "Ridge"}


def hh(s: str) -> int:
    return int(s.split(":")[0])


def window_hours(w: dict) -> list[float]:
    a, b = hh(w["start"]), hh(w["end"])
    return [a, b if b > a else 24]


# ---------------------------------------------------------------- scoring (only when actuals exist)
def score_rows(fc: dict, y: list, from_hour: int) -> list[dict]:
    idx = pd.date_range(fc["day"], periods=24, freq="h")
    ys = pd.Series([np.nan if v is None else v for v in y], index=idx)
    out = []
    for name in ("M1 TabPFN v2", "B2 CAMS+hour bias", "B0 raw CAMS"):
        m = fc["models"][name]
        for view in ("full", "late"):
            fh = 0 if view == "full" else from_hour
            if view == "late" and fh <= 0:
                continue
            sel = idx[idx.hour >= fh]
            yv, p = ys.reindex(sel), pd.Series(m["hourly"], index=idx).reindex(sel)
            both = pd.concat([p, yv], axis=1, keys=["p", "y"]).dropna()
            if len(both) < (20 if fh == 0 else 4):
                continue
            err = both["p"] - both["y"]
            rho = both["p"].corr(both["y"], method="spearman")
            if view == "full":
                cs = pd.Timestamp(f"{fc['day']} {m['windows']['cleanest']['start']}")
            else:
                bp = best_pair(p, True)
                cs = bp[0] if bp else None
            if cs is None:
                continue
            ch = [cs, cs + pd.Timedelta(hours=1)]
            n6 = 6 if fh == 0 else max(2, round(6 * len(sel) / 24))
            clean = set(yv.nsmallest(n6).index)
            act = ys.reindex(ch).mean()
            out.append({"model": LABEL[name], "view": view, "mae": float(err.abs().mean()), "bias": float(err.mean()), "rho": float(rho),
                        "window": f"{cs:%H:%M}-{(ch[1] + pd.Timedelta(hours=1)):%H:%M}", "win_actual": float(act),
                        "day_mean": float(yv.mean()), "hit": set(ch) <= clean, "n": int(len(both)), "clean_n": n6})
    return out


# ---------------------------------------------------------------- html fragments
def esc(x) -> str:
    return html.escape(str(x))


def fmt_table(rows: list[list[str]], head: list[str], cls: str = "") -> str:
    h = "".join(f"<th scope='col'>{esc(c)}</th>" for c in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<div class='tw'><table class='{cls}'><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>"


def build(day: str, actuals_path: Path) -> str:
    fc = json.loads((ROOT / "results" / f"forecast_{day}.json").read_text(encoding="utf-8"))
    lc = json.loads((ROOT / "results" / "learning_curve.json").read_text(encoding="utf-8"))
    te = json.loads((ROOT / "results" / "eval_test.json").read_text(encoding="utf-8"))
    act = json.loads(actuals_path.read_text(encoding="utf-8")) if actuals_path.exists() else None
    late = fc.get("late_entry", {})
    from_hour = int(late.get("from_hour", default_from_hour(fc)))
    M = fc["models"]
    xs24 = [h + 0.5 for h in range(24)]

    # --- forecast chart config
    series = [
        {"name": "TabPFN v2 (late entry)", "key": "tabpfn", "values": M["M1 TabPFN v2"]["hourly"], "w": 2.5},
        {"name": "B2 hour-bias (pre-registered)", "key": "b2", "values": M["B2 CAMS+hour bias"]["hourly"], "w": 2},
        {"name": "B0 raw CAMS (pre-registered)", "key": "b0", "values": M["B0 raw CAMS"]["hourly"], "w": 2, "dash": "5 4"},
    ]
    if act:
        series.append({"name": "Measured (sensor 4554236)", "key": "ink", "values": act["hourly"], "w": 2.5, "markers": True})
    lanes = []
    for name, k in (("M1 TabPFN v2", "tabpfn"), ("B2 CAMS+hour bias", "b2"), ("B0 raw CAMS", "b0")):
        w = M[name]["windows"]
        lanes.append({"label": {"tabpfn": "TabPFN", "b2": "B2", "b0": "B0"}[k], "key": k,
                      "clean": window_hours(w["cleanest"]), "dirty": window_hours(w["dirtiest"]),
                      "cleanTxt": f"{w['cleanest']['start'][:2]}-{w['cleanest']['end'][:2]}", "dirtyTxt": f"{w['dirtiest']['start'][:2]}-{w['dirtiest']['end'][:2]}"})
    forecast_cfg = {"xs": xs24, "xdomain": [0, 24], "ydomain": [0, 100], "yticks": [0, 25, 50, 75, 100], "yunit": "µg/m³",
                    "xticks": [[h, f"{h:02d}"] for h in range(0, 25, 3)], "series": series, "lanes": lanes, "tipx": [f"{h:02d}:00" for h in range(24)],
                    "vlines": [{"x": from_hour, "label": f"{from_hour:02d}:00"}],
                    "bands": [{"x0": 0, "x1": from_hour, "key": "grey"}],
                    "xlabel": "hour of day (Asia/Karachi), predicted PM2.5 at hour start"}

    # --- learning curve configs
    def lc_vals(model: str, metric: str, with_std: bool = False):
        vals, stds = [], []
        for n in LC_N:
            c = lc["curves"].get(model, {}).get(str(n))
            vals.append(None if not c else c[metric]["mean"])
            stds.append(None if not c or c[metric]["std"] is None else c[metric]["std"])
        return (vals, stds) if with_std else vals

    fold_counts = [(lc["curves"]["M1 TabPFN v2"].get(str(n)) or {}).get("MAE", {}).get("n") for n in LC_N]
    xt = [[i, f"{n:,}", f"{fold_counts[i]} folds"] for i, n in enumerate(LC_N)]

    def lc_cfg(metric: str, models: list[str], ydomain, yticks, fmt: str, ylabel: str) -> dict:
        ser = []
        for m in models:
            v, sd = lc_vals(m, metric, True)
            s = {"name": LABEL[m], "key": MODEL_KEY[m], "values": v, "w": 2.5 if m.startswith("M1") else 2, "markers": True}
            if m.startswith("B0"):
                s["dash"] = "5 4"; s["markers"] = False
            if m.startswith("M1"):
                s["whisk"] = True
            s["std"] = sd
            ser.append(s)
        return {"xs": list(range(len(LC_N))), "xdomain": [-0.3, len(LC_N) - 0.7], "ydomain": ydomain, "yticks": yticks, "fmt": fmt, "yunit": "",
                "xticks": xt, "series": ser, "tipx": [f"N = {n:,} training hours" for n in LC_N], "xlabel": "training hours N (the N most recent valid hourly rows before each 30-day test window)",
                "ylabel": ylabel, "bands": [{"x0": 3, "x1": 4, "key": "hl"}], "vlines": []}

    rho_cfg = lc_cfg("rho_median", ["M1 TabPFN v2", "B5 HistGBR", "B2 CAMS+hour bias", "B4 Ridge", "B0 raw CAMS"], [0.2, 0.8], [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8], "0.00",
                     "median within-day Spearman ρ (higher is better)")
    mae_cfg = lc_cfg("MAE", ["M1 TabPFN v2", "B5 HistGBR", "B2 CAMS+hour bias", "B0 raw CAMS"], [0, 50], [0, 10, 20, 30, 40, 50], "0.0",
                     "MAE µg/m³ (lower is better)")

    # --- tables
    def pair_gap(other: str) -> list[str]:
        out = []
        for n in LC_N:
            a, b = lc["curves"]["M1 TabPFN v2"].get(str(n)), lc["curves"].get(other, {}).get(str(n))
            out.append("—" if not a or not b else f"{a['rho_median']['mean'] - b['rho_median']['mean']:+.3f}")
        return out

    lc_rows = []
    for m in ["M1 TabPFN v2", "B5 HistGBR", "B2 CAMS+hour bias", "B4 Ridge", "B0 raw CAMS"]:
        r = [esc(LABEL[m])]
        for n in LC_N:
            c = lc["curves"].get(m, {}).get(str(n))
            r.append("—" if not c else f"{c['rho_median']['mean']:.3f}<br><span class='mut'>MAE {c['MAE']['mean']:.1f}</span>")
        lc_rows.append(r)
    lc_rows.append(["TabPFN − B2 (ρ)"] + pair_gap("B2 CAMS+hour bias"))
    lc_table = fmt_table(lc_rows, ["Model (mean over folds)"] + [f"N={n:,}" for n in LC_N])

    hourly_rows = [[f"{h:02d}:00"] + [f"{M[k]['hourly'][h]:.1f}" for k in ("M1 TabPFN v2", "B2 CAMS+hour bias", "B0 raw CAMS")]
                   + ([("—" if act["hourly"][h] is None else f"{act['hourly'][h]:.1f}")] if act else []) for h in range(24)]
    hourly_table = fmt_table(hourly_rows, ["Hour", "TabPFN v2", "B2", "B0"] + (["Measured"] if act else []))

    win_rows = []
    for name in ("M1 TabPFN v2", "B2 CAMS+hour bias", "B0 raw CAMS"):
        w = M[name]["windows"]
        win_rows.append([esc(LABEL[name]) + (" <span class='tag'>late entry</span>" if name.startswith("M1") else " <span class='tag ok'>pre-registered</span>"),
                         f"{w['cleanest']['start']}–{w['cleanest']['end']} ({w['cleanest']['pm25']})", f"{w['dirtiest']['start']}–{w['dirtiest']['end']} ({w['dirtiest']['pm25']})"])
    win_table = fmt_table(win_rows, ["Model", "Cleanest 2 h (µg/m³)", "Dirtiest 2 h (µg/m³)"])

    hl = M["M1 TabPFN v2"]["windows"]
    claim = (f"Clear Hour predicts the cleanest 2h window of {day} is {hl['cleanest']['start']}-{hl['cleanest']['end']} at {hl['cleanest']['pm25']} ug/m3; "
             f"the dirtiest is {hl['dirtiest']['start']}-{hl['dirtiest']['end']} at {hl['dirtiest']['pm25']} ug/m3.")

    # --- measured/pending block
    if act:
        rows = score_rows(fc, act["hourly"], from_hour)
        trs = []
        for r in rows:
            trs.append([esc(r["model"]), "full day" if r["view"] == "full" else f"hours ≥ {from_hour:02d}:00 (windows re-derived)", f"{r['mae']:.1f}", f"{r['bias']:+.1f}", f"{r['rho']:.3f}",
                        r["window"], f"{r['win_actual']:.1f} vs day mean {r['day_mean']:.1f}", "YES" if r["hit"] else "no"])
        score_block = (f"<p class='note'>Measured hours: {act['n_measured']}/24. Truth = OpenAQ sensor 4554236, uncalibrated low-cost, {esc(act['license'])}, {esc(act['attribution'])}. "
                       f"One day is one sample.</p>" + fmt_table(trs, ["Model", "View", "MAE", "Bias", "Spearman ρ", "Chosen cleanest 2 h", "Actual PM2.5 in that window", "Inside actual cleanest set?"]))
    else:
        score_block = ("<div class='pending' role='status'><strong>Measured (sensor 4554236): Pending - scored after midnight.</strong>"
                       "<p>The measured series and the score table appear here only after <code>scripts/score_forecast.py</code> has been run on the finished day. Nothing on this page is a guess.</p></div>")

    test_rows = []
    for k in ("B0 raw CAMS", "B1 CAMS+const bias", "B2 CAMS+hour bias", "B3 CAMS+hour×season bias", "B4 Ridge", "B5 HistGBR", "M1 TabPFN v2"):
        m = te["metrics"][k]
        test_rows.append([esc(k), f"{m['MAE']:.1f}", f"{m['RMSE']:.1f}", f"{m['Bias']:+.1f}", f"{m['rho_median']:.3f}", f"{m['hit_pct']:.0f}%"])
    test_table = fmt_table(test_rows, ["Model", "MAE", "RMSE", "Bias", "Within-day ρ median", "Top-2h hit"])

    xs = lc["cross_sensor"]["transfer"]
    xs_rows = []
    for k in ("B0 raw CAMS", "B2 CAMS+hour bias", "B4 Ridge", "B5 HistGBR", "M1 TabPFN v2"):
        v = xs[k]
        xs_rows.append([esc(k), f"{v['MAE']['mean']:.1f}", f"{v['rho_median']['mean']:.3f}", f"{v['hit_pct']['mean']:.0f}%", str(v["folds"])])
    xs_table = fmt_table(xs_rows, ["Model", "MAE", "median ρ", "top-window hit", "folds"])

    data = {"forecast": forecast_cfg, "rho": rho_cfg, "mae": mae_cfg}
    return (TEMPLATE.replace("%%DATA%%", json.dumps(data, ensure_ascii=False)).replace("%%DAY%%", esc(day)).replace("%%CLAIM%%", esc(claim))
            .replace("%%FROMHOUR%%", f"{from_hour:02d}:00").replace("%%LATESTAMP%%", esc(late.get("committed_local_approx", "06:51")))
            .replace("%%LCTABLE%%", lc_table).replace("%%HOURLY%%", hourly_table).replace("%%WINTABLE%%", win_table)
            .replace("%%SCOREBLOCK%%", score_block).replace("%%TESTTABLE%%", test_table).replace("%%XSTABLE%%", xs_table).replace("%%REPO%%", REPO)
            .replace("%%MEASURED_LEGEND%%", "<span class='lg'><i class='sw ink'></i>Measured (sensor 4554236)</span>" if act else "<span class='lg'><i class='sw ink'></i>Measured: pending</span>"))


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Clear Hour</title>
<meta name="description" content="Open forecaster ranking the hours of tomorrow by air quality in Islamabad/Rawalpindi. Built with PriorLabs-TabPFN.">
<style>
:root{color-scheme:light;--bg:#fcfcfb;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--mut:#6b6a66;--grid:#e6e5e1;--axis:#c9c8c3;--card:#f4f4f1;--line:#dcdbd6;
--tabpfn:#2a78d6;--hgb:#eb6834;--b2:#1baf7a;--ridge:#eda100;--b0:#7d7c76;--band:rgba(42,120,214,.14);--grey:rgba(120,118,110,.13);--hl:rgba(42,120,214,.07);--pend:#fff7e0;--pendline:#e3c25a;--link:#1c5cab}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])){color-scheme:dark;--bg:#1a1a19;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--mut:#a3a29a;--grid:#2d2d2b;--axis:#444441;--card:#232322;--line:#3a3a37;
--tabpfn:#3987e5;--hgb:#d95926;--b2:#199e70;--ridge:#c98500;--b0:#9a9992;--band:rgba(57,135,229,.2);--grey:rgba(160,158,150,.16);--hl:rgba(57,135,229,.1);--pend:#2c2713;--pendline:#7a6420;--link:#86b6ef}}
:root[data-theme="dark"]{color-scheme:dark;--bg:#1a1a19;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--mut:#a3a29a;--grid:#2d2d2b;--axis:#444441;--card:#232322;--line:#3a3a37;
--tabpfn:#3987e5;--hgb:#d95926;--b2:#199e70;--ridge:#c98500;--b0:#9a9992;--band:rgba(57,135,229,.2);--grey:rgba(160,158,150,.16);--hl:rgba(57,135,229,.1);--pend:#2c2713;--pendline:#7a6420;--link:#86b6ef}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--link)}
.wrap{max-width:860px;margin:0 auto;padding:0 16px 48px}
header{padding:28px 0 8px}
h1{font-size:2rem;margin:0 0 4px;letter-spacing:-.01em}
h2{font-size:1.25rem;margin:36px 0 8px}
h3{font-size:1rem;margin:20px 0 6px}
.sub{color:var(--ink2);margin:0 0 10px}
.badge{display:inline-block;border:1px solid var(--line);background:var(--card);border-radius:999px;padding:3px 12px;font-size:.85rem;font-weight:600}
.callout{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--tabpfn);border-radius:8px;padding:14px 16px;margin:18px 0}
.callout p{margin:0 0 8px}.callout p:last-child{margin:0}
.claim{font-size:1.05rem;font-weight:600}
.note{color:var(--ink2);font-size:.92rem}
.mut{color:var(--mut);font-size:.82rem}
.chart{position:relative;width:100%;margin:6px 0}
.chart svg{display:block;width:100%;height:auto;overflow:visible}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;margin:4px 0 2px;font-size:.88rem;color:var(--ink2)}
.lg{display:inline-flex;align-items:center;gap:6px}
.sw{display:inline-block;width:18px;height:0;border-top:3px solid var(--ink)}
.sw.tabpfn{border-color:var(--tabpfn)}.sw.hgb{border-color:var(--hgb)}.sw.b2{border-color:var(--b2)}.sw.ridge{border-color:var(--ridge)}.sw.ink{border-color:var(--ink)}
.sw.b0{border-top:3px dashed var(--b0)}
.axcap{color:var(--mut);font-size:.78rem;margin:2px 0 0}
.tip{position:absolute;pointer-events:none;background:var(--surface);border:1px solid var(--axis);border-radius:6px;padding:6px 9px;font-size:.82rem;line-height:1.35;box-shadow:0 2px 8px rgba(0,0,0,.18);z-index:3;display:none;max-width:230px}
.tip b{display:block;margin-bottom:2px}
.tip i{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px}
.tw{overflow-x:auto;margin:8px 0}
table{border-collapse:collapse;width:100%;font-size:.88rem}
th,td{text-align:left;padding:5px 9px;border-bottom:1px solid var(--line);vertical-align:top;white-space:nowrap}
th{font-weight:600;color:var(--ink2)}
details{margin:6px 0}summary{cursor:pointer;color:var(--link);font-size:.9rem}
.pending{background:var(--pend);border:1px dashed var(--pendline);border-radius:8px;padding:12px 16px;margin:12px 0}
.pending p{margin:6px 0 0;color:var(--ink2);font-size:.92rem}
.tag{display:inline-block;font-size:.72rem;border:1px solid var(--line);border-radius:4px;padding:0 5px;color:var(--ink2)}
.tag.ok{border-color:var(--b2)}
footer{margin-top:44px;border-top:1px solid var(--line);padding-top:16px;font-size:.85rem;color:var(--ink2)}
footer p{margin:6px 0}
code{background:var(--card);padding:1px 5px;border-radius:4px;font-size:.88em}
svg text{font-family:inherit}
</style>
</head>
<body>
<div class="wrap">
<header>
<h1>Clear Hour</h1>
<p class="sub">An open forecaster that ranks the hours of tomorrow by how breathable the air is in Islamabad / Rawalpindi.</p>
<span class="badge">Built with PriorLabs-TabPFN</span>
</header>

<div class="callout" id="headline">
<p><strong>TabPFN v2 needs roughly 1,000–2,500 training hours (about 6–15 weeks of hourly data) before it matches, and then edges, a one-line hour-of-day bias baseline on hour ranking. Below that it is worse and high-variance.</strong></p>
<p class="note">Mean gap in median within-day ranking ρ, TabPFN − B2: −0.12 at 100 h, −0.05 at 250 h, −0.12 at 500 h, +0.01 at 1,000 h, +0.07 at 2,500 h, +0.11 at 5,000 h. The edge is consistent across folds only at 5,000 h (4/4 folds; 3/5 at 1,000 and 2,500 h). Six rolling-origin folds, not the spent TEST month.</p>
</div>

<h2>Tomorrow's pre-registered forecast: %%DAY%%</h2>
<p class="claim">%%CLAIM%%</p>
<p class="note"><strong>Late entry:</strong> the B0 and B2 curves were committed at 06:10:46 (<a href="%%REPO%%/commit/69c7d9e">69c7d9e</a>). TabPFN was committed at %%LATESTAMP%% (<a href="%%REPO%%/commit/802344a">802344a</a>); hours before that time (shaded, up to %%FROMHOUR%%) had already occurred and are <em>not</em> pre-registered. Inputs are live forecasts; ground truth is an uncalibrated low-cost sensor.</p>
<div class="legend" id="lg-forecast"><span class="lg"><i class="sw tabpfn"></i>TabPFN v2 (late entry)</span><span class="lg"><i class="sw b2"></i>B2 hour-bias</span><span class="lg"><i class="sw b0"></i>B0 raw CAMS</span>%%MEASURED_LEGEND%%</div>
<div class="chart" id="c-forecast" role="img" aria-label="Predicted PM2.5 by hour for three models, with cleanest and dirtiest two-hour windows"></div>
<p class="note">Lanes under the axis: solid bar = each model's cleanest 2 h window, outlined bar = its dirtiest. Shaded region = hours before the TabPFN commit.</p>
%%WINTABLE%%
%%SCOREBLOCK%%
<details><summary>Table view: predicted hourly PM2.5 (µg/m³)</summary>%%HOURLY%%</details>

<h2>Data efficiency: how many hours before a new sensor is usable?</h2>
<p class="note">Rolling-origin test: for each of six 30-day windows, train on the N most recent valid hours before the window (recency, never random). Mean over the folds available at each N (4–6); TabPFN's whiskers are ±1 std across folds (large: fold spread is as big as most gaps between models). The shaded column marks 1,000–2,500 h.</p>
<div class="legend"><span class="lg"><i class="sw tabpfn"></i>TabPFN v2</span><span class="lg"><i class="sw hgb"></i>HistGBR</span><span class="lg"><i class="sw b2"></i>B2 hour-bias</span><span class="lg"><i class="sw ridge"></i>Ridge</span><span class="lg"><i class="sw b0"></i>B0 raw CAMS</span></div>
<h3>Hour ranking (the product metric)</h3>
<div class="chart" id="c-rho" role="img" aria-label="Median within-day Spearman correlation versus training hours for five models"></div>
<h3>Level error</h3>
<div class="chart" id="c-mae" role="img" aria-label="Mean absolute error versus training hours for four models"></div>
<p class="note">Ridge is omitted from the error chart: it is off-scale at small N (MAE 321 at 100 h, 74 at 250 h, 52 at 500 h). N = 10,000 is not shown: TabPFN was not run there (one fold, baselines only). The F3 smog-season fold dominates every mean; differences under ~1–2 µg/m³ or ~0.05 in ρ are ties.</p>
<details><summary>Table view: learning curve</summary>%%LCTABLE%%</details>

<h2>Cross-sensor transfer</h2>
<p class="note">Trained on sensor 4554236 (2,500 most recent hours, no retraining), evaluated at sensor 4565419 over folds F2, F3, F4, F6. Both sensors share the same CAMS/weather inputs; F1 and F5 have no transfer cell.</p>
%%XSTABLE%%

<h2>Held-out TEST month (evaluated once)</h2>
<p class="note">2026-09-10 → 2026-10-09, 30 days, models refit on TRAIN+DEV. TabPFN's MAE edge over B2 is clear; its ranking edge over B2 is <strong>not</strong> statistically significant, and HistGBR beat TabPFN on the DEV month.</p>
%%TESTTABLE%%

<footer>
<p><strong>Built with PriorLabs-TabPFN</strong> (TabPFN v2, Prior Labs License 1.1 — <a href="%%REPO%%/blob/main/docs/licenses/PriorLabs-TabPFN-v2-LICENSE.txt">licence copy</a>). Tinker was not used.</p>
<p>Weather data by <a href="https://open-meteo.com/">Open-Meteo.com</a> (CC BY 4.0). Air-quality model data: Copernicus Atmosphere Monitoring Service (CAMS) via Open-Meteo (see <a href="%%REPO%%/blob/main/docs/attribution.md">attribution</a> for the full CAMS credit). Values were modified by our models.</p>
<p>Air-quality measurements: AirGradient sensors operated via The Urban Unit, CC BY 4.0, from <a href="https://openaq.org/">OpenAQ</a>; uncalibrated, not endorsed by The Urban Unit.</p>
<p><strong>Limitations.</strong> The ground truth is an uncalibrated low-cost sensor, and the evaluation used archived CAMS/weather inputs that are better than live forecasts. One forecast day is an anecdote, and rain or a change in wind can invalidate it.</p>
<p><a href="%%REPO%%">Source and full results</a>.</p>
</footer>
</div>
<script id="data" type="application/json">%%DATA%%</script>
<script>
(function(){
var D=JSON.parse(document.getElementById('data').textContent);
var NS='http://www.w3.org/2000/svg';
function el(n,a,p){var e=document.createElementNS(NS,n);for(var k in a)e.setAttribute(k,a[k]);if(p)p.appendChild(e);return e}
function col(k){return 'var(--'+k+')'}
function fmtv(v,f){if(v==null)return '—';return f==='0.00'?v.toFixed(2):v.toFixed(1)}
function draw(id,cfg){
  var host=document.getElementById(id);host.innerHTML='';
  var W=Math.max(host.clientWidth,260),narrow=W<520;
  var lanes=cfg.lanes||[];
  var ml=narrow?40:48,mr=narrow?10:14,mt=10,mb=cfg.xticks&&cfg.xticks[0].length>2?38:24;
  var ph=narrow?230:290,laneH=lanes.length?lanes.length*20+14:0;
  var H=mt+ph+mb+laneH+(cfg.ylabel?0:0);
  var svg=el('svg',{viewBox:'0 0 '+W+' '+H,width:W,height:H,role:'presentation'});
  host.appendChild(svg);
  var pw=W-ml-mr;
  var x0=cfg.xdomain[0],x1=cfg.xdomain[1];
  function X(v){return ml+(v-x0)/(x1-x0)*pw}
  var y0=cfg.ydomain[0],y1=cfg.ydomain[1];
  function Y(v){return mt+ph-(v-y0)/(y1-y0)*ph}
  var f=cfg.fmt||'0.0';
  (cfg.bands||[]).forEach(function(b){el('rect',{x:X(b.x0),y:mt,width:Math.max(X(b.x1)-X(b.x0),0),height:ph,style:'fill:'+col(b.key)},svg)});
  cfg.yticks.forEach(function(t){
    el('line',{x1:ml,x2:ml+pw,y1:Y(t),y2:Y(t),style:'stroke:'+col('grid')+';stroke-width:1'},svg);
    var tx=el('text',{x:ml-6,y:Y(t)+4,'text-anchor':'end',style:'fill:'+col('mut')+';font-size:11px'},svg);tx.textContent=(f==='0.00'?t.toFixed(1):t);
  });
  el('line',{x1:ml,x2:ml+pw,y1:mt+ph,y2:mt+ph,style:'stroke:'+col('axis')},svg);
  cfg.xticks.forEach(function(t){
    var tx=el('text',{x:X(t[0]),y:mt+ph+16,'text-anchor':'middle',style:'fill:'+col('mut')+';font-size:11px'},svg);tx.textContent=t[1];
    if(t[2]){var t2=el('text',{x:X(t[0]),y:mt+ph+30,'text-anchor':'middle',style:'fill:'+col('mut')+';font-size:10px'},svg);t2.textContent=t[2]}
  });
  var cap=document.createElement('div');cap.className='axcap';
  cap.textContent=(cfg.ylabel?'y: '+cfg.ylabel+(cfg.yunit?' ('+cfg.yunit+')':'')+'  ·  ':(cfg.yunit?'y: '+cfg.yunit+'  ·  ':''))+'x: '+cfg.xlabel;
  (cfg.vlines||[]).forEach(function(v){
    el('line',{x1:X(v.x),x2:X(v.x),y1:mt,y2:mt+ph,style:'stroke:'+col('ink2')+';stroke-width:1.5;stroke-dasharray:3 3'},svg);
    var tx=el('text',{x:X(v.x)+4,y:mt+12,style:'fill:'+col('ink2')+';font-size:11px'},svg);tx.textContent=v.label;
  });
  cfg.series.forEach(function(s){
    var c=col(s.key==='ink'?'ink':s.key);
    if(s.whisk&&s.std){cfg.xs.forEach(function(x,i){var v=s.values[i],sd=s.std[i];if(v==null||sd==null)return;
      var lo=Y(Math.max(v-sd,y0)),hi=Y(Math.min(v+sd,y1)),cx=X(x);
      el('line',{x1:cx,x2:cx,y1:lo,y2:hi,style:'stroke:'+c+';stroke-width:1.5;opacity:.4'},svg);
      el('line',{x1:cx-4,x2:cx+4,y1:lo,y2:lo,style:'stroke:'+c+';stroke-width:1.5;opacity:.4'},svg);
      el('line',{x1:cx-4,x2:cx+4,y1:hi,y2:hi,style:'stroke:'+c+';stroke-width:1.5;opacity:.4'},svg)})}
    var d='',pen=false;
    cfg.xs.forEach(function(x,i){var v=s.values[i];if(v==null){pen=false;return}d+=(pen?'L':'M')+X(x)+','+Y(Math.min(Math.max(v,y0),y1));pen=true});
    el('path',{d:d,fill:'none',style:'stroke:'+c+';stroke-width:'+(s.w||2)+(s.dash?';stroke-dasharray:'+s.dash:'')+';stroke-linejoin:round;stroke-linecap:round'},svg);
    if(s.markers)cfg.xs.forEach(function(x,i){var v=s.values[i];if(v!=null)el('circle',{cx:X(x),cy:Y(Math.min(Math.max(v,y0),y1)),r:4,style:'fill:'+c+';stroke:'+col('surface')+';stroke-width:2'},svg)});
  });
  // direct labels at right end (wide screens only), de-collided
  if(!narrow&&cfg.fmt){
    var ends=[];cfg.series.forEach(function(s){for(var i=s.values.length-1;i>=0;i--){if(s.values[i]!=null){ends.push({s:s,y:Y(s.values[i]),i:i});break}}});
    ends.sort(function(a,b){return a.y-b.y});for(var k=1;k<ends.length;k++){if(ends[k].y-ends[k-1].y<13)ends[k].y=ends[k-1].y+13}
    ends.forEach(function(e){var tx=el('text',{x:Math.min(X(cfg.xs[e.i])+8,W-4),y:e.y+4,'text-anchor':'start',style:'fill:'+col('ink2')+';font-size:11px'},svg);tx.textContent=e.s.name;})
  }
  // lanes: cleanest (solid) and dirtiest (outlined) windows per model
  if(lanes.length){
    var ly=mt+ph+mb;
    lanes.forEach(function(L,i){
      var yy=ly+i*20;
      var lt=el('text',{x:ml-6,y:yy+12,'text-anchor':'end',style:'fill:'+col('ink2')+';font-size:11px'},svg);lt.textContent=L.label;
      el('rect',{x:X(0),y:yy,width:pw,height:16,rx:3,style:'fill:'+col('grid')+';opacity:.5'},svg);
      var cb=el('rect',{x:X(L.clean[0]),y:yy,width:X(L.clean[1])-X(L.clean[0]),height:16,rx:3,style:'fill:'+col(L.key)},svg);
      el('rect',{x:X(L.dirty[0])+1,y:yy+1,width:X(L.dirty[1])-X(L.dirty[0])-2,height:14,rx:3,style:'fill:none;stroke:'+col(L.key)+';stroke-width:2;stroke-dasharray:3 2'},svg);
      if(X(L.clean[1])-X(L.clean[0])>=36){var t1=el('text',{x:X(L.clean[0])+4,y:yy+12,style:'fill:#fff;font-size:10.5px;font-weight:600'},svg);t1.textContent=L.cleanTxt}
      if(X(L.dirty[1])-X(L.dirty[0])>=36){var t2=el('text',{x:X(L.dirty[0])+5,y:yy+12,style:'fill:'+col('ink2')+';font-size:10.5px'},svg);t2.textContent=L.dirtyTxt}
    });
    // faint in-plot echo of each cleanest window
    lanes.forEach(function(L){el('rect',{x:X(L.clean[0]),y:mt,width:X(L.clean[1])-X(L.clean[0]),height:ph,style:'fill:'+col(L.key)+';opacity:.07'},svg)});
  }
  host.appendChild(cap);
  // hover layer: crosshair + tooltip
  var cross=el('line',{y1:mt,y2:mt+ph,style:'stroke:'+col('ink2')+';stroke-width:1;display:none'},svg);
  var tip=document.createElement('div');tip.className='tip';host.appendChild(tip);
  var hit=el('rect',{x:ml,y:mt,width:pw,height:ph,fill:'transparent',style:'cursor:crosshair'},svg);
  function move(ev){
    var r=svg.getBoundingClientRect(),px=(ev.clientX-r.left)*(W/r.width);
    var best=0,bd=1e9;cfg.xs.forEach(function(x,i){var d=Math.abs(X(x)-px);if(d<bd){bd=d;best=i}});
    var cx=X(cfg.xs[best]);cross.setAttribute('x1',cx);cross.setAttribute('x2',cx);cross.style.display='';
    var h='<b>'+cfg.tipx[best]+'</b>';
    cfg.series.forEach(function(s){var v=s.values[best];if(v==null)return;
      var sd=s.std&&s.std[best]!=null?' ± '+fmtv(s.std[best],f):'';
      h+='<div><i style="background:'+col(s.key==='ink'?'ink':s.key)+'"></i>'+s.name+': '+fmtv(v,f)+sd+'</div>'});
    tip.innerHTML=h;tip.style.display='block';
    var left=cx*(r.width/W)+12;if(left+230>r.width)left=cx*(r.width/W)-tip.offsetWidth-12;
    tip.style.left=Math.max(left,0)+'px';tip.style.top='8px';
  }
  hit.addEventListener('pointermove',move);hit.addEventListener('pointerdown',move);
  hit.addEventListener('pointerleave',function(){cross.style.display='none';tip.style.display='none'});
}
function all(){draw('c-forecast',D.forecast);draw('c-rho',D.rho);draw('c-mae',D.mae)}
all();
var t;window.addEventListener('resize',function(){clearTimeout(t);t=setTimeout(all,120)});
})();
</script>
</body>
</html>
"""


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    day = args[0] if args else "2026-10-11"
    ap = Path(sys.argv[sys.argv.index("--actuals") + 1]) if "--actuals" in sys.argv else ROOT / "results" / f"actuals_{day}.json"
    out = ROOT / "docs" / "index.html"
    page = build(day, ap)
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({len(page) / 1024:.0f} KB); actuals: {'present' if ap.exists() else 'ABSENT -> Pending placeholder'}")


if __name__ == "__main__":
    main()
