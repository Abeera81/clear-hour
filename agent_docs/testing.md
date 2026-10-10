# Verification per milestone

| Milestone | Command | Pass condition |
|---|---|---|
| Env | `.venv/Scripts/python -c "import torch,tabpfn,tinker,pandas,sklearn,astral"` | no error; `torch.cuda.is_available()` False is fine |
| Capability probes | `.venv/Scripts/python scripts/probes.py` | each probe ✅ or clearly explained ✗ |
| Data probe | `.venv/Scripts/python scripts/data_probe.py` | writes `results/data_probe.md`, aggregates only |
| Dataset build | {{PLACEHOLDER}} | record counts match API totals; license + source_url on every row |
| Fine-tune | {{PLACEHOLDER}} | dev metric beats baselines |
| Forecaster | {{PLACEHOLDER}} | leave-one-season-out beats baselines |
| Held-out eval (once) | {{PLACEHOLDER}} | results written to `results/`, never re-run for tuning |
| Sunday forecast | `git log -- results/forecast_2026-10-11*` | commit timestamp before outing |
