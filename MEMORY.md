# MEMORY.md — field-window

## What this is
**Clear Hour** — local, open-source forecaster ranking tomorrow's hours by how breathable the air is in Islamabad/Rawalpindi (smog season). TabPFN on years of hourly Open-Meteo air-quality + weather history. A day's forecast is committed to git BEFORE that day, then checked. Primary prize: Best Use of TabPFN; Tinker optional. Deadline 2026-10-12 06:59 UTC. Repo: https://github.com/Abeera81/field-window. Brief: `agent_docs/project_brief.md`.

## Stack
Python (uv venv, 3.12), CPU torch, tinker, tabpfn, pandas, scikit-learn, requests, astral, pydantic, python-dotenv. Windows + Git Bash. Details: `agent_docs/tech_stack.md`.

## Status
- Repo bootstrap + agent docs: implemented; remote origin = https://github.com/Abeera81/field-window
- Env (uv venv py3.12, deps, requirements.txt): tested
- Capability probes: tested; Tinker ✅; TabPFN ✅ on **v2** only (v3.5 download stalls)
- iNaturalist data probe: tested, plan dropped
- Air-quality feasibility probe: tested (`scripts/aq_probe.py` → results/aq_probe.md, 2026-10-10)
- Ground-truth probe (OpenAQ): tested (`scripts/ground_truth_probe.py` → results/ground_truth_probe.md, 2026-10-10)
- Dataset build / features / TabPFN model / committed forecast / scoring: planned

## Capability grid
Run 2026-10-10 ~22:04 PKT, `.venv/Scripts/python scripts/probes.py` (results/probes.md)
- python ✅ 3.12.15 in venv (system 3.14.4)
- disk ✅ 43.9 GB free on D:
- ram ✅ 6.2 GB available of 16.9 GB
- torch ✅ 2.14.1+cpu, cuda=False
- tinker Qwen/Qwen3.5-4B ✅ LoRA r16 client created, tokenizer Qwen/Qwen3.5-4B (tinker 0.33.1)
- tinker Qwen/Qwen3-8B ✅ LoRA r16 client created, tokenizer Qwen/Qwen3-8B
- tabpfn v3.5 ✗ licence OK, but HF download of tabpfn-v3.5-20260909.safetensors stalls every time (804 MB run 1; 0 B run 2; 67 MB with hf_transfer + HF_XET_HIGH_PERFORMANCE, run 3, 8-min timeout). HF_HUB_ENABLE_HF_TRANSFER is deprecated in huggingface_hub 2.2.0 (uses hf_xet)
- tabpfn v2 ✅ `scripts/tabpfn_check.py v2` 2026-10-10: classifier `tabpfn-v2-classifier-finetuned-zk73skhh.ckpt` fit+predict 10 s; regressor `tabpfn-v2-regressor.ckpt` fit+predict 12 s (tabpfn 9.1.0, CPU, fit_with_cache). **Use v2** (`create_default_for_version(ModelVersion.V2)`); v2 weights Apache-2.0 with attribution
- open-meteo ✅ (earlier run) archive 2022-10-09: 24 hourly rows; not reached in latest run

## Data findings
Open-Meteo Air Quality @33.6,73.05 (2026-10-10; results/aq_probe.md):
- Hourly pm2_5 from **2022-08-04** (CAMS global) to yesterday; 36,672 rows, 0.01% null, no gaps >24 h; all 6 pollutants accepted.
- Strong seasonal + diurnal signal: Jan 58, Dec 50, Apr 23 µg/m³; Oct–Dec diurnal min 06h (27.6) / max 21h (66.9), ratio 2.42 (rest of year 1.73).
- forecast_days max 7 (≈6 calendar days of pm2_5); past_days works but returns the SAME CAMS model series as history (diff 0.00) — it is model, not measured.
- Weather archive joins 100% on timestamps (Asia/Karachi, both UTC+5); boundary_layer_height null 2024-01-01→2024-07-01 (4,368 h).
- Artifacts: 2022-12-14/15 daily pm2_5 ~0.8 (implausible) → exclude. Highest days ~110 µg/m³ (Nov 2024).
- License: CC BY 4.0; free API non-commercial, <10k calls/day, 5k/h, 600/min. Must attribute CAMS + Open-Meteo.
Ground truth — OpenAQ v3, bbox ~50 km (results/ground_truth_probe.md):
- 55 locations; only 2 reference-grade, both the **US Embassy Islamabad** BAM (15 km NE of CAMS point): StateAir feed 8634 (2019-05→2025-03-04) + AirNow feed 233470 (2021-08→**2026-02-16**). Merged: 49,875 valid h, 15.6% missing, 48 gaps >24 h. **No reference monitor is live now.**
- 31 current low-cost PM2.5 sites (AirGradient + Hawanama). Best: Rawalpindi Women University 4554236 (AirGradient, 5.2 km): 2025-05-29→now, 2.5% missing, 167/168 h last week, latest reading ~2 h old. Usable to score yesterday/today.
- **CAMS vs embassy (27,993 h overlap 2022-08→2026-02): hourly r 0.555, daily r 0.625, mean error −18.9 µg/m³ (CAMS low), MAE 29.9.** Within-day hour-ranking Spearman median 0.43. Bias is strongly hour- and season-dependent: Oct–Dec CAMS under-reads by ~−20 at night/early morning up to −90 at 09h and −70 at 19–21h (monitor has morning 09h + evening 20h peaks CAMS mostly misses). ⇒ plenty for a correction model to learn.
- CAMS vs low-cost (≈1.3k–12k h, 2025-05→2026-10): r 0.53–0.56, mean error −22 to −37, same hour/season pattern.
- Licences: AirNow feed = US Public Domain; StateAir feed licence null; AirGradient sites = CC BY 4.0, attribution "The Urban Unit". OpenAQ terms: users must follow provider terms and acknowledge original sources; rate limit 60/min (header X-Ratelimit-Limit).
- WAQI/aqicn alternative not checked (OpenAQ had usable data, so the fallback wasn't triggered).

- iNaturalist (birds, 25 km) probed earlier and dropped: 822 records, 92 dates, 5% descriptions.

## Key decisions
- 2026-10-10 PIVOT: iNaturalist bird plan dropped → Clear Hour. Reasons: ~4 competing bird-ID entries already published in this challenge; only 822 research-grade Aves records / 92 distinct dates locally; 5% have descriptions.
- Exclude 2022-12-14/15 (CAMS artifact) from training.
- TabPFN model = v2 (classifier + regressor), local CPU. Not the hosted API.
- Ground truth: embassy BAM (history to 2026-02-16) for training/eval; current low-cost AirGradient sensor(s) needed to score the committed forecast.
- Attribution: Open-Meteo gives no exact AQ string. AQ docs: "All users of Open-Meteo data must provide a clear attribution to CAMS ENSEMBLE data provider as well as a reference to Open-Meteo"; licence page HTML example: "Weather data by Open-Meteo.com". Proposed (ours, not quoted): "Air quality: Copernicus Atmosphere Monitoring Service (CAMS) via Open-Meteo.com; weather data by Open-Meteo.com (CC BY 4.0)."
- venv on Python 3.12 (uv-managed), not system 3.14.
- requirements.txt = `uv pip freeze` + `--extra-index-url` for CPU torch.
- probes.py skips TabPFN without a token (else interactive browser login).
- `.gitignore` uses `data/raw/*` + `!data/raw/.gitkeep` so the dir stays tracked but contents don't.

## Open questions
- Scoring target for the committed forecast: low-cost AirGradient 4554236 (current, but uncalibrated) vs nothing live from the embassy. Calibrate low-cost vs embassy on their overlap (2025-05→2026-02)? {{PLACEHOLDER}}
- Retry TabPFN v3.5 later (HF_TOKEN / different network) or stay on v2? {{PLACEHOLDER}}
- Target definition (pm2_5 per hour? rank of hours?) and baselines: {{PLACEHOLDER}}
- Which day gets the committed forecast: {{PLACEHOLDER}}

## File map
- `AGENTS.md` rules · `CLAUDE.md` pointer · `REVIEW-CHECKLIST.md`
- `agent_docs/` brief, stack, testing
- `scripts/probes.py` capability probes, `scripts/data_probe.py` iNat probe (dropped), `scripts/aq_probe.py` AQ probe (cache data/raw/aq/), `scripts/ground_truth_probe.py` OpenAQ probe (cache data/raw/openaq/), `scripts/tabpfn_check.py <version>` · `src/` lib · `train/` Tinker · `eval/` eval
- `data/raw/` (ignored) · `data/sample/` small redistributable samples · `labels/` · `results/` · `docs/`
