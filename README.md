# Clear Hour

**Built with PriorLabs-TabPFN**

Clear Hour is a local, open-source forecaster that ranks the hours of tomorrow by how breathable the air is in Islamabad / Rawalpindi, so a person can pick the cleanest window to go outside during smog season. It takes the free CAMS air-quality forecast (via Open-Meteo), corrects it with TabPFN v2 trained on a year of readings from a nearby low-cost sensor (via OpenAQ), and predicts hourly PM2.5 at that sensor. A forecast for a specific day is committed to git **before** the day, then scored against what the sensor measured.

Demo page: [`docs/index.html`](docs/index.html) (self-contained; open it in a browser). Screenshots: [phone 390 px](results/demo_390.png), [desktop 1280 px](results/demo_1280.png).

## Headline: how much data does TabPFN need?

> **TabPFN v2 needs roughly 1,000–2,500 training hours (about 6–15 weeks of hourly data) before it matches, and then edges, a one-line hour-of-day bias baseline (B2) on hour ranking. Below that it is worse and high-variance.**

Rolling-origin test, 6 folds of 30 days each, training on the N most recent valid hours before each window (recency, never random), no tuning, not the held-out TEST month. Mean over the folds available at each N (4–6; later folds have more history). Full tables, per-fold numbers, paired differences and limitations: [`results/learning_curve.md`](results/learning_curve.md); plot data: [`results/learning_curve.json`](results/learning_curve.json).

| N (hours) | folds | TabPFN ρ | HistGBR ρ | B2 ρ | raw CAMS ρ | TabPFN MAE | HistGBR MAE | B2 MAE | raw CAMS MAE |
|---|---|---|---|---|---|---|---|---|---|
| 100 | 6 | 0.317 | 0.350 | 0.439 | 0.439 | 19.7 | 18.3 | 19.2 | 24.9 |
| 250 | 6 | 0.447 | 0.402 | 0.498 | 0.439 | 18.4 | 18.8 | 18.1 | 24.9 |
| 500 | 5 | 0.431 | 0.442 | 0.555 | 0.479 | 17.9 | 17.5 | 21.3 | 27.2 |
| 1000 | 5 | 0.544 | 0.441 | 0.535 | 0.479 | 17.2 | 17.2 | 24.1 | 27.2 |
| 2500 | 5 | 0.616 | 0.457 | 0.543 | 0.479 | 16.0 | 16.8 | 30.2 | 27.2 |
| 5000 | 4 | 0.590 | 0.541 | 0.476 | 0.431 | 16.9 | 31.9 | 44.5 | 30.1 |

ρ = median within-day Spearman between predicted and measured hourly PM2.5 (higher is better); MAE in µg/m³. Be careful what this does and does not say:

- **Small N is a negative result.** At 100–500 hours TabPFN is no better than untuned HistGBR on error, and worse than B2 on ranking (mean ρ gap TabPFN − B2: −0.12, −0.05, −0.12). At N=100 its ranking is also the most erratic (ρ ± 0.34 across folds).
- **The edge over B2 is modest and fold-dependent.** Mean ρ gap vs B2 is +0.01 at 1,000 h and +0.07 at 2,500 h (better in only 3 of 5 folds each time), and +0.11 at 5,000 h (4 of 4 folds). The MAE advantage over HistGBR at 1,000–2,500 h is under 1 µg/m³; the larger gap at 5,000 h comes from one fold.
- **Fold spread is as large as most gaps.** The smog-season fold (F3) dominates every mean. Treat differences under ~1–2 µg/m³ or ~0.05 in ρ as ties.
- **N = 10,000 was not tested for TabPFN** here (time budget), only the baselines on one fold.
- **Cost:** TabPFN fit + predict on a CPU laptop takes about 30 s at 100 h, 3 min at 1,000 h, 9 min at 2,500 h and 15 min at 5,000 h; the baselines take under a second.

### Cross-sensor transfer

Trained on sensor 4554236 (the 2,500 most recent hours, **no retraining**) and evaluated at sensor 4565419 (Social Welfare Department, 5.0 km from the CAMS point) over folds F2, F3, F4, F6: **TabPFN MAE 16.8, ρ 0.661, top-window hit 56%**, versus raw CAMS 27.5 / 0.570 / 43%. So a correction learned at one sensor carries over to a neighbouring one. Caveats: both sensors share the same CAMS/weather inputs (only the target differs); F1 and F5 have no transfer cell (not enough history at the source sensor for F1; the target sensor was offline for most of F5); a TabPFN "native" reference (trained on the target sensor itself) was not run, and for the baselines that were run the transfer was not worse than native, for reasons we did not investigate.

## Held-out TEST month (evaluated once)

Task: predict hourly PM2.5 at OpenAQ sensor 4554236 and rank the hours of each day. Split is strictly temporal; TRAIN 2025-05-29 → 2026-08-10, DEV 2026-08-11 → 2026-09-09, TEST 2026-09-10 → 2026-10-09 (30 days, 719 hourly rows). Models were refit on TRAIN+DEV and scored on TEST once. From [`results/evaluation.md`](results/evaluation.md):

| Model | MAE | RMSE | Bias | Within-day ρ median | ρ mean | Days | Top-2h-window hit % | Chosen window actual | Best possible window | Day mean |
|---|---|---|---|---|---|---|---|---|---|---|
| B0 raw CAMS | 16.1 | 20.7 | -3.4 | 0.564 | 0.467 | 30 | 30% | 42.6 | 34.1 | 49.2 |
| B1 CAMS+const bias | 22.0 | 28.7 | +20.2 | 0.564 | 0.467 | 30 | 30% | 42.6 | 34.1 | 49.2 |
| B2 CAMS+hour bias | 22.1 | 28.7 | +20.2 | 0.544 | 0.454 | 30 | 43% | 40.7 | 34.1 | 49.2 |
| B3 CAMS+hour×season bias | 31.6 | 41.1 | +27.3 | 0.489 | 0.407 | 30 | 40% | 41.1 | 34.1 | 49.2 |
| B4 Ridge | 20.3 | 27.4 | +17.4 | 0.603 | 0.512 | 30 | 30% | 41.7 | 34.1 | 49.2 |
| B5 HistGBR | 10.8 | 15.2 | -4.1 | 0.644 | 0.552 | 30 | 40% | 41.2 | 34.1 | 49.2 |
| M1 TabPFN v2 | 10.3 | 14.6 | -4.2 | 0.675 | 0.563 | 30 | 37% | 41.2 | 34.1 | 49.2 |

TabPFN has the lowest MAE and RMSE, and it is clearly better than B2 on MAE (95% CI of the difference −17.0 to −6.9 µg/m³). **Its ranking edge over B2 is not statistically significant** (median ρ 0.675 vs 0.544, 95% CI of the difference −0.039 to +0.291), and **HistGBR beat TabPFN on the DEV month** (MAE 9.1 vs 10.1; median ρ 0.663 vs 0.571). Picking the exact cleanest 2-hour window is hard for every model (30–43% hit rate on TEST).

## Pre-registered forecast: 2026-10-11

- **Stage 1, pre-registration:** B0 (raw CAMS) and B2 (hour-of-day bias) from live forecast inputs, committed at 2026-10-11T06:10:46+05:00 in [`69c7d9e`](https://github.com/Abeera81/field-window/commit/69c7d9e).
- **Stage 2, late entry:** the TabPFN v2 fit takes tens of minutes on CPU, so TabPFN was committed later, at 06:51:41 local, in [`802344a`](https://github.com/Abeera81/field-window/commit/802344a). **Hours before that time had already occurred and are NOT pre-registered for TabPFN.** TabPFN was run on the exact feature matrix fetched at 06:10 (no refetch), and its B0/B2 values were verified identical to stage 1 before the stage-2 commit. That matrix was not saved to disk, so there is no hash for it; the stage-1 JSON hash is recorded in the card.
- The card ([`results/forecast_2026-10-11.md`](results/forecast_2026-10-11.md), [`.json`](results/forecast_2026-10-11.json)) states: *Clear Hour predicts the cleanest 2h window of 2026-10-11 is 15:00-17:00 at 49.2 ug/m3; the dirtiest is 22:00-00:00 at 78.4 ug/m3* (TabPFN). B2 picked the same windows (15:00-17:00 at 54.0; 22:00-00:00 at 81.8); B0 picked 05:00-07:00 at 34.9 as cleanest and 22:00-00:00 at 67.3 as dirtiest.
- On the held-out month the exact-window hit rate was 37% for TabPFN (30% raw CAMS, 43% B2), and live inputs are worse than the archive inputs used in that evaluation.

## Real-world check

{{PENDING: filled after scoring}}

## Limitations

From the evaluation, plus the ones that matter for the live forecast:

- **Ground truth is an uncalibrated low-cost sensor** (AirGradient, OpenAQ 4554236). Absolute µg/m³ errors are relative to this sensor, not to a reference monitor. Against the US Embassy reference monitor (5,385 overlapping hours, up to 2026-02-16) it correlates well (hourly r 0.809, daily r 0.951) but reads 14.7 µg/m³ higher on average.
- **CAMS and weather inputs in the evaluation are archive values, not true day-ahead forecasts.** The Open-Meteo CAMS archive is stitched from the most recent model runs, and the weather archive is reanalysis/best-match. A real day-ahead run uses older forecasts (lead 24–48 h), so live skill will likely be worse than shown here for all CAMS-based models alike.
- **Short history:** the sensor starts 2025-05-29, so TRAIN contains exactly one Oct–Dec smog season (2025). B3's season cells and any seasonal learning rest on that single season.
- **DEV/TEST are 30 days each** (late Aug → early Oct 2026), i.e. the transition into smog season; they say little about mid-winter performance. Bootstrap CIs are by day and so reflect only ~30 independent days.
- **TabPFN context limit:** TabPFN sees at most the most recent 10,000 training rows; older rows are dropped for it (not for the other models).
- **Single location, single sensor:** one AirGradient unit can drift, be moved, or be locally affected; the second sensor is used only for the transfer test.
- CAMS alignment (instantaneous value at hour start vs the monitor's hourly mean) is a fixed convention.
- **One day is an anecdote.** Whatever the 2026-10-11 score turns out to be, it is a single sample and cannot confirm or refute the 30-day results.
- **Rain and wind:** rain washes PM2.5 out of the air and a wind shift can clear or deliver smoke within hours. The models see precipitation and wind as inputs, but they have been trained on a single smog season, and live forecasts of rain timing are uncertain. A rainy day is a likely way for any of these forecasts to be badly wrong.

## What we got wrong

- **A bug in my compute-budget estimator** wrongly skipped all N=5000 and N=10,000 TabPFN fits in the learning-curve run. It extrapolated quadratically from the N=500 timing and projected 200 minutes per fit, when the real cost was 12–22 minutes. I found it in the logs at 84 minutes, fixed the estimator, cleared the five wrongly "not run" cells and **resumed within the original 3-hour budget**. N=5000 then completed on all four eligible folds; N=10,000 was skipped for genuine budget reasons. No result informed that change and the protocol did not change. The same estimator also initially skipped one cross-sensor cell, which I ran afterwards.
- **Fold dates were adjusted before any fit:** the F2 and F3 start dates were nudged by a few days so that N=2,500 and N=5,000 were reachable. This was done before any model ran, and the protocol was committed first, in [`7438bbc`](https://github.com/Abeera81/field-window/commit/7438bbc).
- **I assumed the TabPFN v2 weights were plain Apache-2.0.** They are under the Prior Labs License 1.1 (Apache-2.0 plus a mandatory "Built with PriorLabs-TabPFN" display). Found when reading the licence on 2026-10-11; see [`docs/attribution.md`](docs/attribution.md).
- **The live feature matrix for the 2026-10-11 forecast was never saved or hashed,** so "no refetch" rests on reading the code and on the B0/B2 values matching exactly. Future forecast runs must save the matrix and record its sha256.
- **TabPFN v3.5 would not download** on this machine (the weight download stalled three times), so everything uses TabPFN v2.
- The original idea (bird-identification from iNaturalist records) was dropped before this project began: too few usable local records and several similar entries already existed.

## How to reproduce

Windows + Git Bash. Python 3.12 via `uv`. CPU only (no GPU needed).

```bash
# 1. environment
uv venv --python 3.12
source .venv/Scripts/activate
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
uv pip install -r requirements.txt

# 2. keys (git-ignored .env): copy the template and fill in
cp .env.example .env
#   OPENAQ_API_KEY   required (OpenAQ v3, free)
#   TABPFN_TOKEN     not needed for TabPFN v2; only used by scripts/probes.py
#   TINKER_API_KEY   only used by scripts/probes.py (Tinker is not used for any result)

# 3. dataset: pulls Open-Meteo (CAMS + weather) and OpenAQ sensor 4554236 -> data/processed/hourly.parquet
python -m src.dataset
#    NB: the window ends yesterday, so re-running later gives more rows than the committed results used.
#    The numbers in results/*.json are the record.

# 4. evaluation (TabPFN fit + predict: ~55 min on DEV, ~85 min on TEST, 7-8 GB RAM, 16 GB laptop)
python -m eval.evaluate dev
python -m eval.evaluate test        # refuses to run twice (results/eval_test.json exists); TEST was spent once
python -m eval.evaluate report      # rebuilds results/evaluation.md

# 5. learning curve (resumable; about 3 hours of CPU)
python -m eval.learning_curve run --budget-min 175
python -m eval.learning_curve report

# 6. a pre-registered forecast for a day (live inputs; the TabPFN fit took ~40 min for 10,000 rows)
python -m src.forecast 2026-10-11 stage2            # writes B0/B2 first, then TabPFN
python scripts/finalize_late_entry.py 2026-10-11    # stamps the late-entry wording (stage 2 only)
git add results/forecast_2026-10-11.* && git commit -m "forecast: ..." && git push   # commit BEFORE the day

# 7. after the day is over: score it, then rebuild the demo page
python scripts/score_forecast.py 2026-10-11 [--from-hour 07]
python scripts/build_demo.py 2026-10-11
```

Optional probes that produced the early data findings: `python scripts/probes.py`, `scripts/aq_probe.py`, `scripts/ground_truth_probe.py`, `scripts/tabpfn_check.py v2`.

## Stack

- **TabPFN v2** (regressor, local CPU, no tuning) — Prior Labs; Prior Labs License 1.1, see [`docs/attribution.md`](docs/attribution.md).
- **Open-Meteo** air-quality (CAMS model data) and weather APIs.
- **OpenAQ v3** for sensor measurements.
- scikit-learn (baselines), pandas, numpy, pyarrow, requests.
- **Tinker was NOT used.** (`scripts/probes.py` created LoRA training clients for two models as a capability check; nothing was trained or sampled.) No other sponsor tools.

## Attribution

- **Built with PriorLabs-TabPFN.** TabPFN v2 weights are distributed under the Prior Labs License 1.1 (Apache 2.0 with an additional attribution requirement); a copy is in [`docs/licenses/PriorLabs-TabPFN-v2-LICENSE.txt`](docs/licenses/PriorLabs-TabPFN-v2-LICENSE.txt). Hollmann et al., *Nature* 2025, doi:10.1038/s41586-024-08328-6.
- Weather data by [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0). Air-quality model data: Copernicus Atmosphere Monitoring Service (CAMS) via Open-Meteo. Open-Meteo's page asks users to "provide a clear attribution to CAMS ENSEMBLE data provider as well as a reference to Open-Meteo"; the full CAMS credit list is in [`docs/attribution.md`](docs/attribution.md). Values were modified by our models.
- Air-quality measurements: AirGradient sensors operated via **The Urban Unit**, CC BY 4.0, retrieved from [OpenAQ](https://openaq.org/). This does not imply endorsement by The Urban Unit; the sensor is uncalibrated.
- US Embassy Islamabad monitor (OpenAQ/AirNow feed, US Public Domain) was used only as a validity check.

Code: MIT (see [`LICENSE`](LICENSE)); data and model weights keep their own licences.

## Deadline note

The challenge deadline is **Mon 2026-10-12 06:59 UTC**. Any commit made after that time is listed here:

- *(none as of this writing)*
