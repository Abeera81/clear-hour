# MEMORY.md — field-window

## What this is
Hackathon project (DEV Hacktoberfest Wk1 "Touch Grass", deadline 2026-10-12 06:59 UTC). Real iNaturalist records near Islamabad/Rawalpindi → (a) Tinker LoRA fine-tune, (b) TabPFN outing forecast + Open-Meteo weather. Sunday 2026-10-11 forecast committed before the outing. See `agent_docs/project_brief.md`.

## Stack
Python (uv venv, 3.12), CPU torch, tinker, tabpfn, pandas, scikit-learn, requests, astral, pydantic, python-dotenv. Windows + Git Bash. Details: `agent_docs/tech_stack.md`.

## Status
- Repo bootstrap + agent docs: implemented
- Env + capability probes: planned
- iNaturalist data probe: planned
- Dataset build / fine-tune task / forecaster / Sunday forecast: planned

## Capability grid
_(filled by `scripts/probes.py`)_

## Data findings
_(filled by data probe)_

## Key decisions
- `.gitignore` uses `data/raw/*` + `!data/raw/.gitkeep` so the dir stays tracked but contents don't.

## Open questions
- Fine-tune task definition: {{PLACEHOLDER}}
- Forecast target (species? group? count?): {{PLACEHOLDER}}

## File map
- `AGENTS.md` rules · `CLAUDE.md` pointer · `REVIEW-CHECKLIST.md`
- `agent_docs/` brief, stack, testing
- `scripts/` probes · `src/` lib · `train/` Tinker · `eval/` eval
- `data/raw/` (ignored) · `data/sample/` small redistributable samples · `labels/` · `results/` · `docs/`
