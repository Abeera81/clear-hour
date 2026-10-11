"""python -m clearhour [--date YYYY-MM-DD] [--model b2|tabpfn] [--json] [--save] ...

Ranks the hours of a day by predicted PM2.5 at OpenAQ sensor 4554236 (Rawalpindi/Islamabad) from live CAMS + weather
forecasts. All forecasting logic lives in src/forecast.py; this file is argument parsing and presentation only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from clearhour import __version__

EPA_MODERATE_CEILING = 35.4  # US EPA PM2.5 'Moderate' upper bound, µg/m3
ATTRIBUTION = [
    "Weather data by Open-Meteo.com (CC BY 4.0); air-quality model data: Copernicus Atmosphere Monitoring Service (CAMS) via Open-Meteo.",
    "Sensor data: AirGradient via The Urban Unit (CC BY 4.0), from OpenAQ. Uncalibrated low-cost sensor; not endorsed by The Urban Unit.",
    "Built with PriorLabs-TabPFN",
]
LIMITS = "Predicts PM2.5 at ONE uncalibrated low-cost sensor from live forecasts; ranking is more reliable than absolute level. One day is an anecdote."


def log(msg: str, quiet: bool) -> None:
    if not quiet:
        print(msg, file=sys.stderr, flush=True)


def spark(values: list[float], ascii_only: bool) -> str:
    chars = " .:-=+*#%@" if ascii_only else "▁▂▃▄▅▆▇█"
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1.0
    return "".join(chars[min(int((v - lo) / span * (len(chars) - 1) + 0.5), len(chars) - 1)] for v in values)


def can_print_blocks() -> bool:
    try:
        "▁█".encode(sys.stdout.encoding or "ascii")
        return True
    except (UnicodeEncodeError, LookupError):
        return False


def best_remaining(hourly: list[float], from_hour: int) -> dict | None:
    """Cleanest 2 h window that starts at or after `from_hour` (local)."""
    best = None
    for h in range(from_hour, 23):
        v = (hourly[h] + hourly[h + 1]) / 2
        if best is None or v < best[1]:
            best = (h, v)
    return None if best is None else {"start": f"{best[0]:02d}:00", "end": f"{best[0] + 2:02d}:00" if best[0] + 2 < 24 else "00:00", "pm25": round(best[1], 1)}


def recommendation(day: str, model_label: str, entry: dict, remaining: dict | None, now_h: int | None) -> tuple[str, str | None]:
    c, d = entry["windows"]["cleanest"], entry["windows"]["dirtiest"]
    spread = d["pm25"] - c["pm25"]
    if now_h is not None and int(c["start"][:2]) < now_h and remaining:
        head = (f"The cleanest window ({c['start']}-{c['end']}) has already started or passed; best remaining window today is "
                f"{remaining['start']}-{remaining['end']} (~{remaining['pm25']:.0f} µg/m³).")
    else:
        head = f"Best time to go out: {c['start']}-{c['end']} (~{c['pm25']:.0f} µg/m³)."
    line = f"{head} Avoid {d['start']}-{d['end']} (~{d['pm25']:.0f} µg/m³); the best window is ~{spread:.0f} µg/m³ cleaner than the worst."
    note = None
    if c["pm25"] > EPA_MODERATE_CEILING:
        note = (f"Even the cleanest window is above {EPA_MODERATE_CEILING} µg/m³ (the US EPA 'Moderate' ceiling) at this sensor, which read "
                f"~15 µg/m³ higher than the US Embassy monitor in our comparison; consider limiting strenuous outdoor activity.")
    return line, note


def render(res: dict, ascii_only: bool) -> str:
    day, prim = res["day"], res["primary_model"]
    entry = res["models"][prim]
    h = entry["hourly"]
    L = [f"Clear Hour — {day} (Asia/Karachi) — model: {prim}", ""]
    c, d = entry["windows"]["cleanest"], entry["windows"]["dirtiest"]
    L += [f"  Cleanest 2h window : {c['start']}-{c['end']}   ~{c['pm25']:.1f} µg/m³",
          f"  Dirtiest 2h window : {d['start']}-{d['end']}   ~{d['pm25']:.1f} µg/m³", ""]
    L += [f"  -> {res['recommendation']}"]
    if res.get("recommendation_note"):
        L += [f"     Note: {res['recommendation_note']}"]
    axis = [" "] * 24
    for pos, lab in ((0, "00"), (6, "06"), (12, "12"), (18, "18"), (22, "23")):
        axis[pos:pos + 2] = list(lab)
    L += ["", "  24 h at a glance (low = clean):", "  " + spark(h, ascii_only), "  " + "".join(axis)]
    L += [""]
    for r in range(4):
        L.append("  " + "   ".join(f"{hh:02d}h {h[hh]:5.1f}" for hh in range(r * 6, r * 6 + 6)))
    others = [(k, v) for k, v in res["models"].items() if k != prim]
    if others:
        L += ["", "  Other models, same inputs: " + "; ".join(f"{k}: cleanest {v['windows']['cleanest']['start']}-{v['windows']['cleanest']['end']}" for k, v in others)]
    L += ["", f"  Inputs: live forecast fetched {res['input_meta']['fetched_utc']} UTC; feature matrix {res['input_matrix']['path']}",
          f"          sha256 {res['input_matrix']['sha256']}"]
    if res.get("tabpfn"):
        t = res["tabpfn"]
        L += [f"  TabPFN v2: {t['train_rows']} training rows, {'loaded from cache' if t['cached'] else 'fitted'} in {t['seconds']} s"]
    else:
        L += [f"  B2 hour-bias offsets: {res['b2']['n_rows']} sensor readings up to {res['b2']['last_hour']} ({res['b2']['source']})"]
    L += ["", "-" * 78] + ATTRIBUTION[:2] + ["", LIMITS, ATTRIBUTION[2], f"clearhour {__version__} - generated {res['generated_local']} (Asia/Karachi); commit a saved forecast before the day if you want it pre-registered."]
    return "\n".join(L)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m clearhour", description="Rank the hours of a day by predicted PM2.5 in Islamabad/Rawalpindi.",
                                 epilog="Built with PriorLabs-TabPFN")
    ap.add_argument("--date", metavar="YYYY-MM-DD", help="local (Asia/Karachi) day to forecast; default today. Must be within Open-Meteo's forecast window.")
    ap.add_argument("--model", choices=["b2", "tabpfn"], default="b2",
                    help="b2 (default): CAMS + hour-of-day bias, instant, no key. tabpfn: TabPFN v2 on CPU, ~30-90 min first time, ~8 GB RAM, needs OPENAQ_API_KEY")
    ap.add_argument("--json", action="store_true", help="machine-readable JSON on stdout")
    ap.add_argument("--save", action="store_true", help="write results/forecast_<date>.json (+ the feature matrix in results/inputs/); never overwrites without --force")
    ap.add_argument("--force", action="store_true", help="with --save: overwrite an existing results/forecast_<date>.json")
    ap.add_argument("--refit", action="store_true", help="refit B2 offsets from fresh OpenAQ data (needs OPENAQ_API_KEY) and keep them locally")
    ap.add_argument("--no-cache", action="store_true", help="do not reuse / store the fitted TabPFN model")
    ap.add_argument("--tabpfn-rows", type=int, default=None, metavar="N", help="advanced: TabPFN training context rows (default 10000; smaller is faster but not what the evaluation used)")
    ap.add_argument("--yes", action="store_true", help="do not ask for confirmation before a long TabPFN run")
    ap.add_argument("--ascii", action="store_true", help="ASCII-only sparkline")
    ap.add_argument("--quiet", action="store_true", help="no progress messages on stderr")
    ap.add_argument("--debug", action="store_true", help="show tracebacks")
    ap.add_argument("--version", action="version", version=f"clearhour {__version__}")
    return ap


def run(args: argparse.Namespace) -> int:
    import pandas as pd
    from src import forecast as eng

    q = args.quiet
    today = eng.today_local()
    day = args.date or today
    try:
        dd = datetime.strptime(day, "%Y-%m-%d").date()
    except ValueError:
        raise eng.ForecastError(f"--date must look like 2026-10-12, got '{day}'.")
    t = datetime.strptime(today, "%Y-%m-%d").date()
    if dd < t:
        raise eng.ForecastWindowError(f"{day} is in the past. Clear Hour forecasts today ({today}) and the next few days.")
    if dd > t + timedelta(days=eng.MAX_AHEAD_DAYS - 1):
        raise eng.ForecastWindowError(f"{day} is too far ahead: Open-Meteo's air-quality forecast covers at most {eng.MAX_AHEAD_DAYS} days from today ({today}).")

    use_tabpfn = args.model == "tabpfn"
    rows = args.tabpfn_rows or eng.TABPFN_ROWS
    if (use_tabpfn or args.refit) and not os.environ.get("OPENAQ_API_KEY"):
        raise eng.MissingKeyError("OPENAQ_API_KEY is not set. Training data comes from OpenAQ (free key: https://explore.openaq.org/register). "
                                  "Put it in .env as OPENAQ_API_KEY=... (see .env.example). The default --model b2 needs no key.")
    if use_tabpfn:
        log("NOTE: TabPFN v2 runs locally on CPU. The first run fits 10,000 rows: expect ~30-90 minutes and ~8 GB RAM; "
            "the fitted model is cached, so later runs reuse it.", q)
        if sys.stdin.isatty() and not args.yes and not args.json:
            if input("Continue? [y/N] ").strip().lower() not in ("y", "yes"):
                raise eng.ForecastError("Cancelled. Use the default --model b2 for an instant answer.")

    log(f"Fetching live CAMS air-quality and weather forecasts for {day} ...", q)
    live, meta = eng.live_features(day)

    train = None
    if use_tabpfn or args.refit:
        log("Building the training table from OpenAQ + Open-Meteo (first run takes a minute or two) ...", q)
        train = eng.training_table(day)
    if train is not None and (args.refit or use_tabpfn):
        b2 = eng.fit_b2(train)
        b2["source"] = "fitted on the current training table"
        if args.refit:
            eng.LOCAL_B2.parent.mkdir(parents=True, exist_ok=True)
            eng.LOCAL_B2.write_text(json.dumps({k: v for k, v in b2.items() if k != "source"}, indent=1), encoding="utf-8")
            log(f"Refitted B2 offsets saved to {eng.LOCAL_B2.relative_to(eng.ROOT)}", q)
    else:
        b2, label = eng.load_b2()
        b2["source"] = f"{label} offsets"
        age = (dd - pd.Timestamp(b2["last_hour"]).date()).days
        if age > 45:
            log(f"WARNING: B2 offsets are {age} days old; run `python -m clearhour --refit` (needs OPENAQ_API_KEY) to refresh them.", q)

    matrix_dir = eng.ROOT / ("results/inputs" if args.save else "data/processed/inputs")
    matrix = eng.save_matrix(live, day, matrix_dir, meta["fetched_utc"])

    models = {"B0 raw CAMS": eng.model_entry(live["cams_pm2_5"]), "B2 CAMS+hour bias": eng.model_entry(eng.predict_b2(live, b2))}
    tabpfn_info = None
    if use_tabpfn:
        p, tabpfn_info = eng.predict_tabpfn(train, live, rows, use_cache=not args.no_cache, log=lambda s: log(s, q))
        models = {"M1 TabPFN v2": eng.model_entry(p), **models}
    primary = "M1 TabPFN v2" if use_tabpfn else "B2 CAMS+hour bias"

    now_local = datetime.now(timezone.utc) + eng.LOCAL_OFFSET
    now_h = now_local.hour + (1 if now_local.minute else 0) if day == today else None
    rem = best_remaining(models[primary]["hourly"], now_h) if now_h is not None and now_h < 23 else None
    rec, note = recommendation(day, primary, models[primary], rem, now_h)

    res = {"day": day, "tool": f"clearhour {__version__}", "stage": "cli", "primary_model": primary,
           "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "generated_local": f"{now_local:%Y-%m-%d %H:%M}",
           "input_meta": meta, "input_matrix": matrix, "models": models, "recommendation": rec, "recommendation_note": note,
           "best_remaining_today": rem, "b2": {k: b2[k] for k in ("n_rows", "last_hour", "source")},
           "caveats": eng.caveats(b2["n_rows"], b2["last_hour"], rows if use_tabpfn else None, b2["source"]),
           "attribution": ATTRIBUTION, "limitations": LIMITS}
    if tabpfn_info:
        res["tabpfn"] = tabpfn_info
    if args.save:
        out = eng.ROOT / "results" / f"forecast_{day}.json"
        if out.exists() and not args.force:
            raise eng.ForecastError(f"{out.relative_to(eng.ROOT)} already exists (it may be a committed, pre-registered forecast). "
                                    f"Not overwriting; pass --force to replace it.")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, indent=1), encoding="utf-8")
        res["saved_to"] = str(out.relative_to(eng.ROOT)).replace("\\", "/")
        log(f"Saved {res['saved_to']} and {matrix['path']}", q)

    if args.json:
        print(json.dumps(res, indent=1, ensure_ascii=False))
    else:
        ascii_only = args.ascii or not can_print_blocks()
        text = render(res, ascii_only)
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode("ascii", "replace").decode("ascii"))
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # piped output on Windows defaults to cp1252, which cannot print µ or the sparkline
        if not stream.isatty() and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as e:  # noqa: BLE001
        try:
            from src.forecast import ForecastError
        except Exception:  # noqa: BLE001
            ForecastError = ()  # type: ignore[assignment,misc]
        if args.debug:
            raise
        if isinstance(e, ForecastError):
            print(f"clearhour: error: {e}", file=sys.stderr)
            return 2
        print(f"clearhour: unexpected error: {type(e).__name__}: {e}\n(re-run with --debug for the traceback)", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
