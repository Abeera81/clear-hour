# Clear Hour

**Built with PriorLabs-TabPFN**

Clear Hour is a local, open-source forecaster that ranks the hours of tomorrow by how breathable the air is in Islamabad / Rawalpindi, so a person can pick the cleanest window to go outside during smog season. It takes the free CAMS air-quality forecast (via Open-Meteo), corrects it with TabPFN v2 trained on a year of readings from a nearby low-cost sensor (via OpenAQ), and predicts hourly PM2.5 at that sensor. A forecast for a specific day is committed to git **before** the day, then scored against what the sensor measured.

Demo page: [`docs/index.html`](docs/index.html) (self-contained; open it in a browser). Screenshots: [phone 390 px](results/demo_390.png), [desktop 1280 px](results/demo_1280.png).

## Try it

`clearhour` ranks the hours of a day by predicted PM2.5 at the sensor, from live CAMS + weather forecasts. After the install steps in [How to reproduce](#how-to-reproduce) (step 1 only):

```bash
python -m clearhour                      # today, instant (B2 hour-of-day bias on live CAMS); no API key needed
python -m clearhour --date 2026-10-13    # a specific day; works for today and the next few days
python -m clearhour --json               # machine-readable
python -m clearhour --save               # also writes results/forecast_<date>.json + the feature matrix with its sha256
python -m clearhour --model tabpfn       # TabPFN v2: ~30-90 min on CPU the first time, ~8 GB RAM, needs OPENAQ_API_KEY
```

- `--save` never overwrites an existing `results/forecast_<date>.json` (it may be a committed, pre-registered forecast) unless you pass `--force`.
- Every run saves the exact 24 x 26 feature matrix as a CSV (`results/inputs/` with `--save`, otherwise `data/processed/inputs/`), named with its fetch time, and prints its sha256, so a forecast can be audited later.
- The fitted TabPFN model is cached in `data/processed/model_cache/` (git-ignored; it is large: 0.3 GB at 500 rows, **6.3 GB** at 10,000), so a repeat run reloads it (about 2 minutes) instead of refitting (about 56 minutes here). Predictions from the reloaded model match the fitted one to within 0.07 µg/m³. `--no-cache` turns that off.
- Default B2 uses 24 hour-of-day offsets packaged in `src/clearhour/b2_offsets.json` (fitted on 11,693 sensor readings up to 2026-10-10 22:00; they reproduce the committed pre-registered B2 exactly). `--refit` re-fits them from fresh OpenAQ data.
- The dates it accepts are today up to the last day for which Open-Meteo has a complete air-quality forecast (through 2026-10-15 when checked, i.e. today + 4 days). Output is for one uncalibrated low-cost sensor; ranking is more reliable than the absolute level.

Real terminal output (captured 2026-10-11, Windows, Git Bash; the first line goes to stderr):

<details><summary>Today (default model, B2): <code>python -m clearhour</code></summary>

```text
Fetching live CAMS air-quality and weather forecasts for 2026-10-11 ...
Clear Hour — 2026-10-11 (Asia/Karachi) — model: B2 CAMS+hour bias

  Cleanest 2h window : 15:00-17:00   ~54.0 µg/m³
  Dirtiest 2h window : 22:00-00:00   ~81.8 µg/m³

  -> Best time to go out: 15:00-17:00 (~54 µg/m³). Avoid 22:00-00:00 (~82 µg/m³); that is ~28 µg/m³ worse than the best window.
     Note: Even the cleanest window is above 35.4 µg/m³ (the US EPA 'Moderate' ceiling) at this sensor, which read ~15 µg/m³ higher than the US Embassy monitor in our comparison; consider limiting strenuous outdoor activity.

  24 h at a glance (low = clean):
  ▂▃▂▂▂▂▃▄▄▄▄▅▄▃▂▁▁▂▄▅▅▆▇█
  00    06    12    18  23

  00h  58.5   01h  60.9   02h  58.6   03h  56.7   04h  56.9   05h  56.8
  06h  60.0   07h  65.2   08h  66.5   09h  65.3   10h  67.1   11h  69.5
  12h  65.8   13h  61.5   14h  57.8   15h  53.1   16h  54.9   17h  59.0
  18h  67.0   19h  70.9   20h  71.5   21h  73.7   22h  78.8   23h  84.8

  Other models, same inputs: B0 raw CAMS: cleanest 05:00-07:00

  Inputs: live forecast fetched 2026-10-11T07:30:07+00:00 UTC; feature matrix data/processed/inputs/forecast_inputs_2026-10-11_20261011T073007Z.csv
          sha256 227fcdb3de19e9cb03f820314ebc2c8dbed39e392b47f5abeefb9693addc19ba
  B2 hour-bias offsets: 11693 sensor readings up to 2026-10-10 22:00:00 (packaged offsets)

------------------------------------------------------------------------------
Weather data by Open-Meteo.com (CC BY 4.0); air-quality model data: Copernicus Atmosphere Monitoring Service (CAMS) via Open-Meteo.
Sensor data: AirGradient via The Urban Unit (CC BY 4.0), from OpenAQ. Uncalibrated low-cost sensor; not endorsed by The Urban Unit.

Predicts PM2.5 at ONE uncalibrated low-cost sensor from live forecasts; ranking is more reliable than absolute level. One day is an anecdote.
Built with PriorLabs-TabPFN
clearhour 0.1.0 - generated 2026-10-11 12:30 (Asia/Karachi); commit a saved forecast before the day if you want it pre-registered.
```
</details>

<details><summary>A future date: <code>python -m clearhour --date 2026-10-13</code></summary>

```text
Fetching live CAMS air-quality and weather forecasts for 2026-10-13 ...
Clear Hour — 2026-10-13 (Asia/Karachi) — model: B2 CAMS+hour bias

  Cleanest 2h window : 15:00-17:00   ~49.0 µg/m³
  Dirtiest 2h window : 00:00-02:00   ~101.3 µg/m³

  -> Best time to go out: 15:00-17:00 (~49 µg/m³). Avoid 00:00-02:00 (~101 µg/m³); that is ~52 µg/m³ worse than the best window.
     Note: Even the cleanest window is above 35.4 µg/m³ (the US EPA 'Moderate' ceiling) at this sensor, which read ~15 µg/m³ higher than the US Embassy monitor in our comparison; consider limiting strenuous outdoor activity.

  24 h at a glance (low = clean):
  ██▆▄▄▃▄▄▄▄▃▃▃▂▁▁▁▂▃▄▄▄▃▂
  00    06    12    18  23

  00h 103.0   01h  99.7   02h  88.3   03h  75.4   04h  68.4   05h  66.4
  06h  68.1   07h  73.4   08h  73.8   09h  68.2   10h  65.8   11h  66.8
  12h  62.5   13h  56.9   14h  50.0   15h  48.2   16h  49.7   17h  55.8
  18h  66.5   19h  70.2   20h  75.2   21h  72.9   22h  65.3   23h  58.2

  Other models, same inputs: B0 raw CAMS: cleanest 14:00-16:00

  Inputs: live forecast fetched 2026-10-11T07:30:11+00:00 UTC; feature matrix data/processed/inputs/forecast_inputs_2026-10-13_20261011T073011Z.csv
          sha256 d9903440d415db9369057c6b377e39725c846c663c8973de4a4d45cf4a1d39ab
  B2 hour-bias offsets: 11693 sensor readings up to 2026-10-10 22:00:00 (packaged offsets)

------------------------------------------------------------------------------
Weather data by Open-Meteo.com (CC BY 4.0); air-quality model data: Copernicus Atmosphere Monitoring Service (CAMS) via Open-Meteo.
Sensor data: AirGradient via The Urban Unit (CC BY 4.0), from OpenAQ. Uncalibrated low-cost sensor; not endorsed by The Urban Unit.

Predicts PM2.5 at ONE uncalibrated low-cost sensor from live forecasts; ranking is more reliable than absolute level. One day is an anecdote.
Built with PriorLabs-TabPFN
clearhour 0.1.0 - generated 2026-10-11 12:30 (Asia/Karachi); commit a saved forecast before the day if you want it pre-registered.
```
</details>

<details><summary>Errors are one clear line, exit code 2, no traceback</summary>

```text
$ python -m clearhour --date 2026-10-09
clearhour: error: 2026-10-09 is in the past. Clear Hour forecasts today (2026-10-11) and the next few days.
$ python -m clearhour --date 2026-10-16
clearhour: error: Open-Meteo does not yet have a complete air-quality forecast for 2026-10-16. The latest hour with data is 2026-10-15 17:00 (local); try a date up to 2026-10-15.
$ HTTPS_PROXY=http://127.0.0.1:9 python -m clearhour   # simulated: no network
Fetching live CAMS air-quality and weather forecasts for 2026-10-11 ...
clearhour: error: Cannot reach air-quality-api.open-meteo.com (ProxyError). Check your internet connection and try again.
$ OPENAQ_API_KEY= python -m clearhour --model tabpfn --yes   # key missing
clearhour: error: OPENAQ_API_KEY is not set. Training data comes from OpenAQ (free key: https://explore.openaq.org/register). Put it in .env as OPENAQ_API_KEY=... (see .env.example). The default --model b2 needs no key.
$ python -m clearhour --date 2026-10-11 --save   # a committed forecast exists
clearhour: error: results\forecast_2026-10-11.json already exists (it may be a committed, pre-registered forecast). Not overwriting; pass --force to replace it.
```
</details>

<details><summary>TabPFN, full 10,000-row context: <code>python -m clearhour --model tabpfn --yes</code> (first run: fitted, 56 min wall clock)</summary>

```text
NOTE: TabPFN v2 runs locally on CPU. The first run fits 10,000 rows: expect ~30-90 minutes and ~8 GB RAM; the fitted model is cached, so later runs reuse it.
Fetching live CAMS air-quality and weather forecasts for 2026-10-11 ...
Building the training table from OpenAQ + Open-Meteo (first run takes a minute or two) ...
fitting TabPFN v2 on 10000 rows (this is the slow step) ...
Clear Hour — 2026-10-11 (Asia/Karachi) — model: M1 TabPFN v2

  Cleanest 2h window : 15:00-17:00   ~49.2 µg/m³
  Dirtiest 2h window : 22:00-00:00   ~78.4 µg/m³

  -> Best time to go out: 15:00-17:00 (~49 µg/m³). Avoid 22:00-00:00 (~78 µg/m³); the best window is ~29 µg/m³ cleaner than the worst.
     Note: Even the cleanest window is above 35.4 µg/m³ (the US EPA 'Moderate' ceiling) at this sensor, which read ~15 µg/m³ higher than the US Embassy monitor in our comparison; consider limiting strenuous outdoor activity.

  24 h at a glance (low = clean):
  ▄▅▃▃▂▂▂▂▃▃▃▃▂▃▂▁▁▃▅▆▇▇██
  00    06    12    18  23

  00h  63.4   01h  64.3   02h  57.6   03h  55.7   04h  53.3   05h  51.3
  06h  51.4   07h  53.3   08h  55.3   09h  57.4   10h  57.2   11h  56.2
  12h  55.2   13h  56.9   14h  52.5   15h  49.6   16h  48.8   17h  59.4
  18h  65.1   19h  69.9   20h  73.5   21h  74.9   22h  78.8   23h  78.1

  Other models, same inputs: B0 raw CAMS: cleanest 05:00-07:00; B2 CAMS+hour bias: cleanest 15:00-17:00

  Inputs: live forecast fetched 2026-10-11T06:25:52+00:00 UTC; feature matrix data/processed/inputs/forecast_inputs_2026-10-11_20261011T062552Z.csv
          sha256 55a8a4c4c3597c21b2b9231fa93f16758057fa8694919019d6684e5a8638b064
  TabPFN v2: 10000 training rows, fitted in 3351 s

------------------------------------------------------------------------------
Weather data by Open-Meteo.com (CC BY 4.0); air-quality model data: Copernicus Atmosphere Monitoring Service (CAMS) via Open-Meteo.
Sensor data: AirGradient via The Urban Unit (CC BY 4.0), from OpenAQ. Uncalibrated low-cost sensor; not endorsed by The Urban Unit.

Predicts PM2.5 at ONE uncalibrated low-cost sensor from live forecasts; ranking is more reliable than absolute level. One day is an anecdote.
Built with PriorLabs-TabPFN
clearhour 0.1.0 - generated 2026-10-11 12:22 (Asia/Karachi); commit a saved forecast before the day if you want it pre-registered.
```
This is the real first run on this laptop (CPU, 16 GB RAM): fit 3,351 s, 56 min 27 s in total. Its inputs had not changed since the pre-registered forecast, and it reproduced the committed TabPFN late-entry windows exactly (15:00-17:00 at 49.2; 22:00-00:00 at 78.4). The fitted model was then cached on disk: **6.3 GB** (it stores the transformer cache for all 10,000 rows).
</details>

<details><summary>Repeat run reuses the cache (118 s to load instead of ~56 min to fit), and live inputs move</summary>

A second run an hour later loaded the cached model in 118 s (2 min 39 s total) and printed `TabPFN v2: 10000 training rows, loaded from cache in 118 s`. Its answer was different (cleanest 05:00-07:00 at ~52.2, dirtiest 22:00-00:00 at ~78.2) **because the live weather forecast had been updated in between**: the feature-matrix hash changed from `55a8a4c4...` (06:25 UTC) to `227fcdb3...` (07:22 UTC). Comparing the two saved matrices, 8 of the 26 features changed, all of them weather (boundary-layer height by up to 695 m, relative humidity by up to 17 points, wind, pressure, temperature, and forecast precipitation +0.3 mm); the CAMS pollutant inputs were identical, which is why the B2 answer did not move at all. To check the cache itself, I fed the cached model the *first* run's saved matrix: it reproduces the freshly fitted predictions to within 0.074 µg/m³ (5 of 24 hourly values differ in the second decimal; not bit-for-bit), far below the 1.5 µg/m³ margins that decide the windows. Two lessons: TabPFN's pick is sensitive to the weather forecast (boundary-layer height in particular), and a live forecast moves when its inputs update, so commit the one you want to be judged on before the day; and a reduced context (`--tabpfn-rows 500`: 55 s fit, 308 MB cache) is available as a quick smoke test but is not what the evaluation used.
</details>

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
- **`requirements.txt` was not installable by anyone else.** It carried the PyTorch CPU `--extra-index-url` line and a `torch==2.14.1+cpu` pin, which makes `uv` refuse PyPI versions of other packages (`certifi` ...). I only found out by installing from a fresh clone while building the CLI. Torch is now its own pinned install step.
- **TabPFN v3.5 would not download** on this machine (the weight download stalled three times), so everything uses TabPFN v2.
- The original idea (bird-identification from iNaturalist records) was dropped before this project began: too few usable local records and several similar entries already existed.

## How to reproduce

Windows + Git Bash. Python 3.12 via `uv`. CPU only (no GPU needed).

```bash
# 1. environment
uv venv --python 3.12
source .venv/Scripts/activate
uv pip install "torch==2.14.1" --index-url https://download.pytorch.org/whl/cpu
uv pip install -r requirements.txt
uv pip install -e .                   # installs the `clearhour` command (python -m clearhour)

# 2. keys (git-ignored .env): copy the template and fill in
cp .env.example .env
#   OPENAQ_API_KEY   required (OpenAQ v3, free)
#   TABPFN_TOKEN     not needed for TabPFN v2; only used by scripts/probes.py
#   TINKER_API_KEY   only used by scripts/probes.py (Tinker is not used for any result)

# 3. (everything below is optional if you only want `python -m clearhour`)
#    dataset: pulls Open-Meteo (CAMS + weather) and OpenAQ sensor 4554236 -> data/processed/hourly.parquet
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
- scikit-learn (baselines), pandas, numpy, pyarrow, requests. The `clearhour` command (`src/clearhour/`) is a thin front end over the shared engine in `src/forecast.py`.
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
