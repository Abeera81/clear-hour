"""Fit TabPFN classifier + regressor on tiny dummy data for one model version.

Usage: .venv/Scripts/python scripts/tabpfn_check.py v3.5|v2|...
Never prints secrets.
"""
from __future__ import annotations

import sys
import time
from importlib.metadata import version
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from tabpfn import TabPFNClassifier, TabPFNRegressor  # noqa: E402
from tabpfn.constants import ModelVersion  # noqa: E402


def main(v: str) -> int:
    mv = ModelVersion(v)
    rng = np.random.default_rng(0)
    X = rng.normal(size=(20, 3))
    ok = True
    for name, cls, y in (("classifier", TabPFNClassifier, np.array([0, 1] * 10)),
                         ("regressor", TabPFNRegressor, X[:, 0] * 2 + rng.normal(size=20) * 0.1)):
        t = time.time()
        try:
            m = cls.create_default_for_version(mv, device="cpu", fit_mode="fit_with_cache")
            m.fit(X, y)
            pred = m.predict(X[:3])
            print(f"[OK] {name} {mv.value}: model_path={m.model_path} pred={np.round(pred, 2).tolist()} "
                  f"({time.time() - t:.0f}s, tabpfn {version('tabpfn')})", flush=True)
        except Exception as e:
            ok = False
            print(f"[FAIL] {name} {mv.value}: {type(e).__name__}: {str(e).splitlines()[0][:200]}", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "v3.5"))
