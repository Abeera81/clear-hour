# MEMORY.md — field-window

## What this is
Hackathon project (DEV Hacktoberfest Wk1 "Touch Grass", deadline 2026-10-12 06:59 UTC). Real iNaturalist records near Islamabad/Rawalpindi → (a) Tinker LoRA fine-tune, (b) TabPFN outing forecast + Open-Meteo weather. Sunday 2026-10-11 forecast committed before the outing. See `agent_docs/project_brief.md`.

## Stack
Python (uv venv, 3.12), CPU torch, tinker, tabpfn, pandas, scikit-learn, requests, astral, pydantic, python-dotenv. Windows + Git Bash. Details: `agent_docs/tech_stack.md`.

## Status
- Repo bootstrap + agent docs: implemented
- Env (uv venv py3.12, deps, requirements.txt): tested (`scripts/probes.py` imports OK)
- Capability probes: implemented; system/torch/Open-Meteo tested; Tinker + TabPFN blocked on missing .env keys
- iNaturalist data probe: tested (`scripts/data_probe.py` → results/data_probe.md, 2026-10-10)
- GitHub repo/push: blocked (gh not authenticated)
- Dataset build / fine-tune task / forecaster / Sunday forecast: planned

## Capability grid
Run 2026-10-10 via `.venv/Scripts/python scripts/probes.py` (full table: results/probes.md)
- python ✅ 3.12.15 in venv (system python is 3.14.4; venv pinned to 3.12 for wheel compat)
- disk ✅ 44.0 GB free on D:
- ram ✅ 5.7 GB available of 16.9 GB
- torch ✅ 2.14.1+cpu, cuda=False
- tinker ✗ TINKER_API_KEY not in .env (no .env yet). Qwen/Qwen3.5-4B + Qwen/Qwen3-8B both untested
- tabpfn ✗ TABPFN_TOKEN not in .env; tabpfn 9.1.0 without token launches browser login (fails headless) → probe skips. Model version unknown
- open-meteo ✅ archive 2022-10-09 @33.7,73.1: 24 hourly rows, pressure 1007.4–1013.3 hPa, cloud 0–11%

## Data findings
iNat research-grade, 25 km around 33.72,73.06 (2026-10-10; results/data_probe.md):
- 2399 obs all taxa; 822 Aves; 159 bird species; only 92 distinct Aves observation dates.
- Aves strongly recent: 2024=160, 2025=328, 2026=160; ≤57/yr before 2024. Sep–Nov (all years): 101.
- Sample 600 Aves: 94% have time_observed_at; only 5% have descriptions (median ~80 chars) → free text too sparse for a text fine-tune task.
- Licenses (sample): cc-by-nc 462, null 81 (all rights reserved: no redistribution), cc-by-nc-nd 43, cc0 14. No cc-by.
- Margalla Hills NP place_id=240339: 824 all taxa, 356 Aves, similar time/license profile.
- Implication: forecaster has few seasons for leave-one-season-out; Tinker task likely must use structured fields (taxon/date/time/place), not descriptions.

## Key decisions
- venv on Python 3.12 (uv-managed), not system 3.14.
- requirements.txt = `uv pip freeze` + `--extra-index-url` for CPU torch.
- probes.py skips TabPFN without a token (else interactive browser login).
- `.gitignore` uses `data/raw/*` + `!data/raw/.gitkeep` so the dir stays tracked but contents don't.

## Open questions
- Fine-tune task definition: {{PLACEHOLDER}}
- Forecast target (species? group? count?): {{PLACEHOLDER}}
- Widen area/taxa (all taxa, or GBIF/eBird) given only 822 Aves / 92 dates? {{PLACEHOLDER}}
- GitHub username for repo: {{PLACEHOLDER}} (gh auth pending)

## File map
- `AGENTS.md` rules · `CLAUDE.md` pointer · `REVIEW-CHECKLIST.md`
- `agent_docs/` brief, stack, testing
- `scripts/probes.py` capability probes, `scripts/data_probe.py` iNat probe (data/raw/probe_sample_aves.json, ignored) · `src/` lib · `train/` Tinker · `eval/` eval
- `data/raw/` (ignored) · `data/sample/` small redistributable samples · `labels/` · `results/` · `docs/`
