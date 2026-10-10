"""Capability probes: system, Tinker, TabPFN, Open-Meteo. Re-runnable.

Usage: .venv/Scripts/python scripts/probes.py
Writes results/probes.md. Never prints secrets.
"""
from __future__ import annotations

import ctypes
import os
import platform
import shutil
import sys
import traceback
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

rows: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, note: str) -> None:
    rows.append((name, ok, note))
    print(f"[{'OK' if ok else 'FAIL'}] {name}: {note}", flush=True)


def redact(msg: str) -> str:
    for var in ("TINKER_API_KEY", "TABPFN_TOKEN"):
        val = os.environ.get(var)
        if val:
            msg = msg.replace(val, "***")
    return msg


def short_err(e: BaseException) -> str:
    return redact(f"{type(e).__name__}: {e}".splitlines()[0][:200])


def pkg(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "not installed"


def probe_system() -> None:
    record("python", True, f"{sys.version.split()[0]} ({platform.platform()})")
    du = shutil.disk_usage(ROOT)
    record("disk", True, f"{du.free / 1e9:.1f} GB free of {du.total / 1e9:.1f} GB on {ROOT.anchor}")
    if os.name == "nt":
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = MEMORYSTATUSEX()
        m.dwLength = ctypes.sizeof(m)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        record("ram", True, f"{m.ullAvailPhys / 1e9:.1f} GB available of {m.ullTotalPhys / 1e9:.1f} GB")
    try:
        import torch
        record("torch", True, f"{torch.__version__}, cuda={torch.cuda.is_available()}")
    except Exception as e:
        record("torch", False, short_err(e))


def probe_tinker() -> None:
    if not os.environ.get("TINKER_API_KEY"):
        record("tinker", False, "TINKER_API_KEY missing/empty in .env")
        return
    import tinker

    service = tinker.ServiceClient()
    for model in ("Qwen/Qwen3.5-4B", "Qwen/Qwen3-8B"):
        try:
            tc = service.create_lora_training_client(base_model=model, rank=16)
            tok = tc.get_tokenizer()
            record(f"tinker {model}", True,
                   f"LoRA r16 client ok; tokenizer={getattr(tok, 'name_or_path', type(tok).__name__)} (tinker {pkg('tinker')})")
        except Exception as e:
            record(f"tinker {model}", False, short_err(e))


def probe_tabpfn() -> None:
    if not os.environ.get("TABPFN_TOKEN"):
        # Without a token tabpfn falls back to an interactive browser login; skip to stay headless.
        record("tabpfn", False, f"TABPFN_TOKEN missing/empty in .env (tabpfn {pkg('tabpfn')} installed; skipped to avoid browser login)")
        return
    try:
        import numpy as np
        from tabpfn import TabPFNClassifier

        rng = np.random.default_rng(0)
        X = rng.normal(size=(10, 3))
        y = np.array([0, 1] * 5)
        clf = TabPFNClassifier(fit_mode="fit_with_cache", device="cpu")
        clf.fit(X, y)
        pred = clf.predict(X[:2])
        model_info = getattr(clf, "model_path", None)
        record("tabpfn", True,
               f"tabpfn {pkg('tabpfn')}; fit+predict ok ({pred.tolist()}); model_path={model_info}; "
               f"token {'set' if os.environ.get('TABPFN_TOKEN') else 'not set'}")
    except Exception as e:
        traceback.print_exc()
        record("tabpfn", False, short_err(e))


def probe_open_meteo() -> None:
    import requests

    try:
        r = requests.get(
            "https://archive-api.open-meteo.com/v1/archive",
            params={"latitude": 33.7, "longitude": 73.1, "start_date": "2022-10-09",
                    "end_date": "2022-10-09", "hourly": "pressure_msl,cloud_cover",
                    "timezone": "Asia/Karachi"},
            timeout=30,
        )
        r.raise_for_status()
        h = r.json()["hourly"]
        n = len(h["time"])
        p, c = h["pressure_msl"], h["cloud_cover"]
        record("open-meteo", n == 24 and None not in p,
               f"{n} hourly rows; pressure_msl {min(p)}-{max(p)} hPa; cloud_cover {min(c)}-{max(c)}%")
    except Exception as e:
        record("open-meteo", False, short_err(e))


def main() -> None:
    for probe in (probe_system, probe_tinker, probe_tabpfn, probe_open_meteo):
        try:
            probe()
        except Exception as e:
            record(probe.__name__, False, short_err(e))
    out = ROOT / "results" / "probes.md"
    lines = ["| Probe | | Note |", "|---|---|---|"]
    lines += [f"| {n} | {'✅' if ok else '✗'} | {note.replace('|', '/')} |" for n, ok, note in rows]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
