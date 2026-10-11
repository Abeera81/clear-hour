"""Stamp the stage-2 forecast card/JSON with the late-entry statement, right before its commit.

Usage: .venv/Scripts/python scripts/finalize_late_entry.py 2026-10-11
The stage-2 process was started before this wording was required, so the statement is added here. Refuses to run
on a stage-1 file. The time written is the time this script runs; the commit follows within seconds (git log is authoritative).
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRE_REG = "B0 and B2 were committed at 06:10:46."


def main(day: str) -> None:
    jp, mp = ROOT / "results" / f"forecast_{day}.json", ROOT / "results" / f"forecast_{day}.md"
    fc = json.loads(jp.read_text(encoding="utf-8"))
    if not str(fc["stage"]).startswith("stage2"):
        sys.exit(f"Refusing: forecast file is '{fc['stage']}', not stage 2.")
    if fc.get("late_entry"):
        sys.exit("Refusing: late-entry statement already present.")
    now_local = datetime.now(timezone.utc) + timedelta(hours=5)  # Asia/Karachi
    stamp = f"{now_local:%H:%M}"
    from_hour = min(24, math.ceil(now_local.hour + now_local.minute / 60 + now_local.second / 3600))
    statement = (f"Late entry: TabPFN committed at {stamp} (Asia/Karachi, {now_local:%Y-%m-%d}). Hours before that time had "
                 f"already occurred and are NOT pre-registered. {PRE_REG}")
    fc["late_entry"] = {"statement": statement, "committed_local_approx": stamp, "from_hour": from_hour,
                        "pre_registered_models": ["B0 raw CAMS", "B2 CAMS+hour bias"], "pre_registered_commit": "69c7d9e",
                        "pre_registered_at_local": "2026-10-11T06:10:46+05:00"}
    jp.write_text(json.dumps(fc, indent=1), encoding="utf-8")
    lines = mp.read_text(encoding="utf-8").splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith("Generated "))
    lines[i + 1:i + 1] = ["", f"> **{statement}**", ">", f"> Frozen inputs: stage 2 used the feature matrix fetched at "
                          f"{fc['input_meta']['fetched_utc']} UTC (06:10 local) with no live refetch."]
    mp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(statement)
    print(f"from_hour={from_hour}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "2026-10-11")
