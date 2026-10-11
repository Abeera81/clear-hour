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
- Dataset (`src/dataset.py` → data/processed/hourly.parquet, 11,669 rows, 26 features): tested (built 2026-10-10)
- Evaluation (`eval/evaluate.py dev|test|report` → results/evaluation.md): tested. DEV run then TEST run ONCE (2026-10-11 ~01:08 PKT); results/eval_test.json exists, so the held-out TEST set is spent
- Forecast 2026-10-11: stage 1 (B0 raw CAMS + B2 hour-bias) committed `69c7d9e` at 2026-10-11T06:10:46+05:00 = the pre-registration. Stage 2 (TabPFN v2) = LATE ENTRY, fit running since 06:10 (~85 min CPU), committed when done; hours before its commit are NOT pre-registered. Stage 2 TabPFN late entry fit finished 2026-10-11 06:51 local (2,421 s fit+predict); B0/B2 verified identical to stage 1 before commit. Status: implemented (both stages pushed; not yet scored)
- Learning curve (`eval/learning_curve.py run|report` → results/learning_curve.{md,json,_cells.json}): tested 2026-10-11 (protocol committed `7438bbc` before any fit; 6 rolling-origin folds, N=100..5000 complete on eligible folds, N=10000 TabPFN not run, cross-sensor transfer on F2/F3/F4/F6). Headline: TabPFN v2 does NOT beat HistGBR/B2 at N<=500; consistent advantage (mostly on within-day ranking) from N~1000-2500; MAE margin over HistGBR <1 ug/m3 there. Status: tested
- README + demo page + attribution (2026-10-11): implemented/tested. `scripts/build_demo.py` -> docs/index.html (self-contained, light/dark, checked in headless Edge at 390 px via iframe and 1280 px; actuals branch tested with SYNTHETIC data only, never committed); screenshots results/demo_390.png, results/demo_1280.png. README 'Real-world check' = {{PENDING: filled after scoring}}. `score_forecast.py` now also writes results/actuals_<date>.json (tested only on synthetic data in a temp dir).
- Scoring (`scripts/score_forecast.py DATE [--from-hour HH]`): implemented; logic self-tested on synthetic data only, NOT yet run on real data (run after the day ends)

## Capability grid
Run 2026-10-10 ~22:04 PKT, `.venv/Scripts/python scripts/probes.py` (results/probes.md)
- python ✅ 3.12.15 in venv (system 3.14.4)
- disk ✅ 43.9 GB free on D:
- ram ✅ 6.2 GB available of 16.9 GB
- torch ✅ 2.14.1+cpu, cuda=False
- tinker Qwen/Qwen3.5-4B ✅ LoRA r16 client created, tokenizer Qwen/Qwen3.5-4B (tinker 0.33.1)
- tinker Qwen/Qwen3-8B ✅ LoRA r16 client created, tokenizer Qwen/Qwen3-8B
- tabpfn v3.5 ✗ licence OK, but HF download of tabpfn-v3.5-20260909.safetensors stalls every time (804 MB run 1; 0 B run 2; 67 MB with hf_transfer + HF_XET_HIGH_PERFORMANCE, run 3, 8-min timeout). HF_HUB_ENABLE_HF_TRANSFER is deprecated in huggingface_hub 2.2.0 (uses hf_xet)
- tabpfn v2 ✅ `scripts/tabpfn_check.py v2` 2026-10-10: classifier `tabpfn-v2-classifier-finetuned-zk73skhh.ckpt` fit+predict 10 s; regressor `tabpfn-v2-regressor.ckpt` fit+predict 12 s (tabpfn 9.1.0, CPU, fit_with_cache). **Use v2** (`create_default_for_version(ModelVersion.V2)`); v2 weights licence = Prior Labs License 1.1 (see Key decisions; NOT plain Apache-2.0)
- open-meteo ✅ (earlier run) archive 2022-10-09: 24 hourly rows; not reached in latest run

## Data findings
Open-Meteo Air Quality @33.6,73.05 (2026-10-10; results/aq_probe.md):
- Hourly pm2_5 from **2022-08-04** (CAMS global) to yesterday; 36,672 rows, 0.01% null, no gaps >24 h; all 6 pollutants accepted.
- Strong seasonal + diurnal signal: Jan 58, Dec 50, Apr 23 µg/m³; Oct–Dec diurnal min 06h (27.6) / max 21h (66.9), ratio 2.42 (rest of year 1.73).
- forecast_days max 7 (≈6 calendar days of pm2_5); past_days works but returns the SAME CAMS model series as history (diff 0.00) — it is model, not measured.
- Weather archive joins 100% on timestamps (Asia/Karachi, both UTC+5); boundary_layer_height null 2024-01-01→2024-07-01 (4,368 h).
- Artifacts: 2022-12-14/15 daily pm2_5 ~0.8 (implausible) → exclude. Highest days ~110 µg/m³ (Nov 2024).
- License: CC BY 4.0; free API non-commercial, <10k calls/day, 5k/h, 600/min. Must attribute CAMS + Open-Meteo.
Evaluation (results/evaluation.md; TRAIN 2025-05-29→2026-08-10, DEV 08-11→09-09, TEST 09-10→10-09):
- DEV: HistGBR best (MAE 9.1, ρ 0.663); TabPFN MAE 10.1, ρ 0.571; B2 MAE 32.3, ρ 0.614; raw CAMS best top-window hit (63%).
- TEST (once): TabPFN best MAE 10.3 / RMSE 14.6 / median within-day ρ 0.675 (CI 0.53–0.78); HistGBR 10.8 / 0.644; B2 22.1 / 0.544; raw CAMS 16.1 / 0.564. TabPFN beats B2 on MAE (diff CI [-17.0,-6.9]); ranking vs B2 not significant (diff CI [-0.04,0.29]). Top-2h-window hit: B2 43%, TabPFN 37%, raw CAMS 30%.
- Bias baselines over-correct out of winter: TRAIN mean(monitor−CAMS) +25.7 vs DEV −6.6, TEST +3.4.
- Validity: sensor vs embassy 5,385 h overlap, hourly r 0.81, daily r 0.95, sensor +14.7 µg/m³ higher (ratio 1.21).
- TabPFN v2 CPU fit+predict ~55–85 min (10k context rows, ~7–8 GB RAM).

Ground truth — OpenAQ v3, bbox ~50 km (results/ground_truth_probe.md):
- 55 locations; only 2 reference-grade, both the **US Embassy Islamabad** BAM (15 km NE of CAMS point): StateAir feed 8634 (2019-05→2025-03-04) + AirNow feed 233470 (2021-08→**2026-02-16**). Merged: 49,875 valid h, 15.6% missing, 48 gaps >24 h. **No reference monitor is live now.**
- 31 current low-cost PM2.5 sites (AirGradient + Hawanama). Best: Rawalpindi Women University 4554236 (AirGradient, 5.2 km): 2025-05-29→now, 2.5% missing, 167/168 h last week, latest reading ~2 h old. Usable to score yesterday/today.
- **CAMS vs embassy (27,993 h overlap 2022-08→2026-02): hourly r 0.555, daily r 0.625, mean error −18.9 µg/m³ (CAMS low), MAE 29.9.** Within-day hour-ranking Spearman median 0.43. Bias is strongly hour- and season-dependent: Oct–Dec CAMS under-reads by ~−20 at night/early morning up to −90 at 09h and −70 at 19–21h (monitor has morning 09h + evening 20h peaks CAMS mostly misses). ⇒ plenty for a correction model to learn.
- CAMS vs low-cost (≈1.3k–12k h, 2025-05→2026-10): r 0.53–0.56, mean error −22 to −37, same hour/season pattern.
- Licences: AirNow feed = US Public Domain; StateAir feed licence null; AirGradient sites = CC BY 4.0, attribution "The Urban Unit". OpenAQ terms: users must follow provider terms and acknowledge original sources; rate limit 60/min (header X-Ratelimit-Limit).
- WAQI/aqicn alternative not checked (OpenAQ had usable data, so the fallback wasn't triggered).

- iNaturalist (birds, 25 km) probed earlier and dropped: 822 records, 92 dates, 5% descriptions.

## Key decisions
- LICENCE FINDING 2026-10-11 (read from files/pages, docs/attribution.md): tabpfn package 9.1.0 code = Apache-2.0; v2 weights (HF Prior-Labs/TabPFN-v2-reg and -clf, LICENSE.txt sha256 08b1851b...) = Prior Labs License 1.1 (Apache-2.0 + paragraph 10). Para 10: when distributing/making available the Work or a product/service containing weights, (A) provide a copy of the licence and (B) prominently display "Built with PriorLabs-TabPFN" on each related website, UI, blogpost, about page, product docs; if weights/outputs are used to create/train/fine-tune/distil an AI model that is distributed, name must begin with "TabPFN". Internal benchmarking is exempt. DONE: licence copy in docs/licenses/, wording in README + docs/index.html header/footer. MUST ALSO: put "Built with PriorLabs-TabPFN" in the DEV post.
- Open-Meteo/CAMS attribution quoted verbatim in docs/attribution.md; their citation names the CAMS European ENSEMBLE product while our point uses the CAMS global domain (no separate global wording on the page) - we credit both. OpenAQ sensors: CC BY 4.0, attribution holder "The Urban Unit".
- README headline framing (user-directed): TabPFN needs ~1,000-2,500 training hours (~6-15 weeks; 2500 h = 14.9 wk, not 14) before it matches then edges B2 on hour ranking; below that worse and high-variance. Gap vs B2 (rho): -0.12/-0.05/-0.12 at 100/250/500, +0.01 (3/5 folds) at 1000, +0.07 (3/5) at 2500, +0.11 (4/4) at 5000.
- RULE for all future forecast runs: save the full feature matrix to disk (e.g. data/processed/forecast_inputs_<date>.parquet) at fetch time and record its sha256 in the forecast JSON/card and here. The 2026-10-11 run did not (see frozen-inputs note below).
- Forecast 2026-10-11 inputs (frozen): `src/forecast.py` fetched the live CAMS + weather-forecast feature matrix ONCE at 2026-10-11T01:10:07Z (06:10:07 local); stage 1 and the stage-2 TabPFN predict() both read that same in-memory table (code: `live_features()` called once, `m.predict(live[feats])`); no refetch. LIMITATION: the full 26-feature matrix was never written to disk, so there is no matrix file/sha256. Anchor instead: committed stage-1 JSON `results/forecast_2026-10-11.json` @ `69c7d9e`, blob sha256 `85a2e07470e249b2215d0b3cf2a19f079ba0f79603982dd483126c5712ecd03d` (holds fetch time, B0/B2 hourly, and cams_pm2_5 / temperature / BLH inputs). Future runs should persist the matrix and hash it.
- Stage-2 card/commit wording is fixed: "Late entry: TabPFN committed at <time>. Hours before that time had already occurred and are NOT pre-registered. B0 and B2 were committed at 06:10:46." Stamped by `scripts/finalize_late_entry.py` (the running stage-2 process predates this wording). Commit message: "forecast: TabPFN late entry (stage 2) for 2026-10-11".
- 2026-10-10 GREEN LIGHT decisions (user):
  - Ground truth = OpenAQ location 4554236 (Rawalpindi Women University, AirGradient, 5.2 km, CC BY 4.0, attribution "The Urban Unit"). Stated publicly as an UNCALIBRATED LOW-COST sensor. Embassy monitor (dead since 2026-02-16) used only as a validity check.
  - Model = TabPFN v2 (licence corrected 2026-10-11: Prior Labs License 1.1 = Apache-2.0 + mandatory "Built with PriorLabs-TabPFN" display; see docs/attribution.md). Stop retrying v3.5; partial v3.5 downloads deleted 2026-10-10.
  - Task = correct CAMS to predict hourly PM2.5 at that sensor, then RANK the hours of a day. Product metric = within-day Spearman.
- Split: TEST = last 30 days, DEV = 30 days before, TRAIN = earlier; TEST evaluated once (eval/evaluate.py refuses a second run). For TEST all models refit on TRAIN+DEV (pre-registered).
- TabPFN on CPU needs `ignore_pretraining_limits=True` for >1,000 rows; context capped at most recent 10,000 rows; ~55 min per fit+predict.
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
- Which day gets the committed forecast: {{PLACEHOLDER}}

## File map
- `AGENTS.md` rules · `CLAUDE.md` pointer · `REVIEW-CHECKLIST.md`
- `agent_docs/` brief, stack, testing
- `scripts/probes.py` capability probes, `scripts/data_probe.py` iNat probe (dropped), `scripts/aq_probe.py` AQ probe (cache data/raw/aq/), `scripts/ground_truth_probe.py` OpenAQ probe (cache data/raw/openaq/), `scripts/tabpfn_check.py <version>`, `src/dataset.py`, `src/forecast.py`, `scripts/score_forecast.py`, `scripts/finalize_late_entry.py`, `docs/outing_log.md` (empty template), `docs/attribution.md`, `docs/licenses/`, `docs/index.html`, `scripts/build_demo.py`, `eval/evaluate.py` (writes results/eval_{dev,test}.json + evaluation.md); data/processed/ ignored · `src/` lib · `train/` Tinker · `eval/` eval
- `data/raw/` (ignored) · `data/sample/` small redistributable samples · `labels/` · `results/` · `docs/`
