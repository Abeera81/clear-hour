# Clear Hour — data-efficiency learning curve

## Protocol (declared before any fit was run; not to be edited after results exist)

**Question.** A new air sensor comes online in this city. After how many hours of data is each model usable?
TabPFN v2's claim is strong performance on small tabular data with no tuning; the earlier evaluation only
tested it at 10,000 training rows. This experiment tests it across training sizes.

**Task, features, target.** Unchanged from `results/evaluation.md`: predict hourly PM2.5 at OpenAQ sensor 4554236
(Rawalpindi Women University, uncalibrated low-cost AirGradient) from the same 26 forecast-available features in
`data/processed/hourly.parquet` (CAMS + weather archive + calendar). No monitor reading is a feature.

**Not the spent TEST split.** All evaluation windows end on or before 2026-09-09. The TEST month (2026-09-10 →
2026-10-09) is not used. The last fold's window coincides with the DEV split used in the earlier evaluation
(that split was used for the earlier model comparison, which this experiment does not tune on).

**Rolling-origin folds (6).** Each fold = a 30-day evaluation window (start date inclusive, 30 consecutive days).
Training = the N valid hourly rows immediately before the window start (recency-based, no random subsampling, no
data from inside or after the window). This simulates a sensor installed N valid hours before the window.

| Fold | Evaluation window (local dates) |
|---|---|
| F1 | 2025-06-13 → 2025-07-12 |
| F2 | 2025-09-18 → 2025-10-17 |
| F3 | 2026-01-04 → 2026-02-02 |
| F4 | 2026-03-23 → 2026-04-21 |
| F5 | 2026-06-12 → 2026-07-11 |
| F6 | 2026-08-11 → 2026-09-09 |

(Start dates were nudged by a few days from a first even spacing, before any model ran, so that F2 and F3 have
≥2,500 and ≥5,000 rows of history available.) A cell (fold, N) is skipped if fewer than N valid rows exist before
the window start; skipped cells are listed in the results. N=10,000 can only exist for F6, so its spread is undefined.

**Training sizes N.** 100, 250, 500, 1000, 2500, 5000, 10000.

**Models at every (fold, N).**
- M1 TabPFN v2: `TabPFNRegressor.create_default_for_version(ModelVersion.V2, device="cpu", fit_mode="fit_with_cache", ignore_pretraining_limits=True, random_state=0)`, no tuning, all 26 features.
- B5 HistGBR: `HistGradientBoostingRegressor(random_state=0)` defaults.
- B4 Ridge: median imputation + standardisation + `Ridge(alpha=1.0)`.
- B2 CAMS + hour-of-day mean bias (fit on the N training rows; hours unseen in training fall back to the global mean bias).
- B0 raw CAMS: no training; one value per fold, reported as a constant reference line (aggregated over the same folds that exist at each N).

**Metrics per cell** (identical definitions to `eval/evaluate.py`): MAE, RMSE, median within-day Spearman
(days with ≥20 hours), top-2h-window hit % (model's lowest-predicted 2 consecutive hours both inside the day's 6
lowest actual hours). Also wall-clock fit time and predict time per (model, N).

**Aggregation.** Mean and standard deviation across the folds available at each (model, N), always with the
number of folds; per-fold numbers are reported too. Because the set of folds changes with N (later folds have
more history), the headline curves mix fold difficulty with N. To control for this, the report also gives
**paired per-fold differences** (TabPFN − B2, TabPFN − HistGBR, TabPFN − B4) at each N and in how many folds
TabPFN is better. Conclusions are drawn from the paired differences.

**Pre-declared reading rules.**
- A model is "usable" at N if its mean MAE over the available folds is below B0 raw CAMS's mean MAE over the same folds.
- TabPFN "wins at N" only if its MAE is lower than every other trained model's MAE in a majority of the folds
  available at N (paired). Ranking skill is judged the same way on median within-day Spearman.
- If TabPFN does not win at small N, that is reported plainly and prominently. Nothing is tuned after seeing results.

**Compute and ordering.** 3-hour wall-clock budget. Phase 1: all models at N ≤ 2500, all folds. Phase 2: N=5000.
Phase 3: N=10000. Phase 4 (only if time remains): cross-sensor transfer. No new fit is started after the budget
is exhausted; cells not completed are listed as missing, never estimated.

**Cross-sensor transfer (Phase 4).** Train on sensor 4554236 (most recent 2,500 rows before each fold's window),
no retraining, evaluate on sensor 4565419 (Social Welfare Department, 5.0 km from the CAMS point) over the same
fold windows, with the same metrics. Same CAMS/weather features (same grid point); only the target differs.
If time allows, a native reference (train on sensor 4565419's own preceding 2,500 rows) is added for comparison.

<!-- RESULTS BELOW -->

# Results

Generated 2026-10-11 10:55 local by `eval/learning_curve.py report`.

### MAE (µg/m³) (mean ± std over folds; n folds in brackets)

| N | B0 raw CAMS | B2 CAMS+hour bias | B4 Ridge | B5 HistGBR | M1 TabPFN v2 |
|---|---|---|---|---|---|
| 100 | 24.9 ± 28.6 [6] | 19.2 ± 12.4 [6] | 320.9 ± 706.9 [6] | 18.3 ± 14.7 [6] | 19.7 ± 17.0 [6] |
| 250 | 24.9 ± 28.6 [6] | 18.1 ± 13.8 [6] | 74.1 ± 115.3 [6] | 18.8 ± 18.6 [6] | 18.4 ± 18.3 [6] |
| 500 | 27.2 ± 31.3 [5] | 21.3 ± 18.0 [5] | 52.5 ± 23.5 [5] | 17.5 ± 15.5 [5] | 17.9 ± 15.0 [5] |
| 1000 | 27.2 ± 31.3 [5] | 24.1 ± 18.2 [5] | 50.5 ± 51.7 [5] | 17.2 ± 14.5 [5] | 17.2 ± 14.7 [5] |
| 2500 | 27.2 ± 31.3 [5] | 30.2 ± 22.0 [5] | 19.1 ± 14.2 [5] | 16.8 ± 13.8 [5] | 16.0 ± 13.8 [5] |
| 5000 | 30.1 ± 35.4 [4] | 44.5 ± 14.4 [4] | 22.4 ± 14.2 [4] | 31.9 ± 27.7 [4] | 16.9 ± 15.4 [4] |
| 10000 | 12.3 (1 fold) [1] | 32.9 (1 fold) [1] | 14.0 (1 fold) [1] | 9.0 (1 fold) [1] | — |

### RMSE (µg/m³) (mean ± std over folds; n folds in brackets)

| N | B0 raw CAMS | B2 CAMS+hour bias | B4 Ridge | B5 HistGBR | M1 TabPFN v2 |
|---|---|---|---|---|---|
| 100 | 30.9 ± 33.6 [6] | 24.9 ± 16.4 [6] | 416.2 ± 927.2 [6] | 23.8 ± 20.3 [6] | 24.7 ± 21.5 [6] |
| 250 | 30.9 ± 33.6 [6] | 23.4 ± 16.9 [6] | 96.5 ± 152.1 [6] | 24.1 ± 24.4 [6] | 22.9 ± 22.1 [6] |
| 500 | 33.6 ± 36.9 [5] | 26.6 ± 20.9 [5] | 63.1 ± 27.3 [5] | 23.2 ± 21.6 [5] | 22.8 ± 19.0 [5] |
| 1000 | 33.6 ± 36.9 [5] | 29.3 ± 21.0 [5] | 59.5 ± 59.5 [5] | 22.6 ± 19.7 [5] | 21.9 ± 18.7 [5] |
| 2500 | 33.6 ± 36.9 [5] | 36.1 ± 22.9 [5] | 25.0 ± 19.4 [5] | 22.5 ± 19.4 [5] | 21.3 ± 19.2 [5] |
| 5000 | 36.9 ± 41.7 [4] | 51.3 ± 19.3 [4] | 29.7 ± 20.4 [4] | 38.5 ± 31.2 [4] | 23.0 ± 22.0 [4] |
| 10000 | 16.1 (1 fold) [1] | 35.8 (1 fold) [1] | 17.9 (1 fold) [1] | 11.4 (1 fold) [1] | — |

### Median within-day Spearman ρ (per-fold median, then averaged) (mean ± std over folds; n folds in brackets)

| N | B0 raw CAMS | B2 CAMS+hour bias | B4 Ridge | B5 HistGBR | M1 TabPFN v2 |
|---|---|---|---|---|---|
| 100 | 0.439 ± 0.208 [6] | 0.439 ± 0.142 [6] | 0.309 ± 0.229 [6] | 0.350 ± 0.225 [6] | 0.317 ± 0.336 [6] |
| 250 | 0.439 ± 0.208 [6] | 0.498 ± 0.142 [6] | 0.470 ± 0.167 [6] | 0.402 ± 0.164 [6] | 0.447 ± 0.217 [6] |
| 500 | 0.479 ± 0.204 [5] | 0.555 ± 0.086 [5] | 0.529 ± 0.127 [5] | 0.442 ± 0.139 [5] | 0.431 ± 0.245 [5] |
| 1000 | 0.479 ± 0.204 [5] | 0.535 ± 0.068 [5] | 0.469 ± 0.187 [5] | 0.441 ± 0.151 [5] | 0.544 ± 0.122 [5] |
| 2500 | 0.479 ± 0.204 [5] | 0.543 ± 0.112 [5] | 0.453 ± 0.169 [5] | 0.457 ± 0.153 [5] | 0.616 ± 0.075 [5] |
| 5000 | 0.431 ± 0.200 [4] | 0.476 ± 0.125 [4] | 0.547 ± 0.165 [4] | 0.541 ± 0.136 [4] | 0.590 ± 0.112 [4] |
| 10000 | 0.602 (1 fold) [1] | 0.610 (1 fold) [1] | 0.604 (1 fold) [1] | 0.622 (1 fold) [1] | — |

### Top-2h-window hit % (exact cleanest 2h inside actual cleanest 6h) (mean ± std over folds; n folds in brackets)

| N | B0 raw CAMS | B2 CAMS+hour bias | B4 Ridge | B5 HistGBR | M1 TabPFN v2 |
|---|---|---|---|---|---|
| 100 | 42 ± 11 [6] | 44 ± 13 [6] | 37 ± 12 [6] | 33 ± 24 [6] | 38 ± 20 [6] |
| 250 | 42 ± 11 [6] | 48 ± 15 [6] | 36 ± 19 [6] | 44 ± 13 [6] | 40 ± 10 [6] |
| 500 | 44 ± 12 [5] | 51 ± 18 [5] | 42 ± 18 [5] | 37 ± 5 [5] | 40 ± 11 [5] |
| 1000 | 44 ± 12 [5] | 53 ± 19 [5] | 45 ± 13 [5] | 38 ± 10 [5] | 50 ± 12 [5] |
| 2500 | 44 ± 12 [5] | 49 ± 13 [5] | 45 ± 9 [5] | 45 ± 4 [5] | 55 ± 9 [5] |
| 5000 | 43 ± 13 [4] | 52 ± 10 [4] | 42 ± 21 [4] | 49 ± 4 [4] | 56 ± 7 [4] |
| 10000 | 63 (1 fold) [1] | 57 (1 fold) [1] | 37 (1 fold) [1] | 50 (1 fold) [1] | — |

### Per-fold MAE

| N | Model | F1 | F2 | F3 | F4 | F5 | F6 |
|---|---|---|---|---|---|---|---|
| 100 | B2 CAMS+hour bias | 14.7 | 13.2 | 43.8 | 12.3 | 19.5 | 11.6 |
| 100 | B4 Ridge | 32.4 | 36.9 | 1763.8 | 39.4 | 24.2 | 28.6 |
| 100 | B5 HistGBR | 13.3 | 12.7 | 48.3 | 11.4 | 11.9 | 12.2 |
| 100 | M1 TabPFN v2 | 13.1 | 12.4 | 54.4 | 11.7 | 14.6 | 12.0 |
| 250 | B2 CAMS+hour bias | 14.1 | 14.7 | 46.0 | 10.8 | 12.7 | 10.5 |
| 250 | B4 Ridge | 49.3 | 21.4 | 308.3 | 20.8 | 16.0 | 29.1 |
| 250 | B5 HistGBR | 12.8 | 13.4 | 56.7 | 8.9 | 10.3 | 10.9 |
| 250 | M1 TabPFN v2 | 12.4 | 11.5 | 55.6 | 9.8 | 9.9 | 11.0 |
| 500 | B2 CAMS+hour bias | skip | 16.9 | 53.3 | 14.6 | 11.8 | 10.1 |
| 500 | B4 Ridge | skip | 22.4 | 65.2 | 72.8 | 32.0 | 70.1 |
| 500 | B5 HistGBR | skip | 12.9 | 45.1 | 8.7 | 9.8 | 11.0 |
| 500 | M1 TabPFN v2 | skip | 13.1 | 44.5 | 10.7 | 9.3 | 11.6 |
| 1000 | B2 CAMS+hour bias | skip | 17.6 | 55.4 | 23.6 | 13.6 | 10.5 |
| 1000 | B4 Ridge | skip | 16.3 | 116.1 | 97.1 | 13.4 | 9.5 |
| 1000 | B5 HistGBR | skip | 14.0 | 42.9 | 9.0 | 9.7 | 10.5 |
| 1000 | M1 TabPFN v2 | skip | 12.3 | 43.3 | 12.0 | 8.1 | 10.2 |
| 2500 | B2 CAMS+hour bias | skip | 17.3 | 41.5 | 63.5 | 16.6 | 11.8 |
| 2500 | B4 Ridge | skip | 14.1 | 43.8 | 17.6 | 11.1 | 8.9 |
| 2500 | B5 HistGBR | skip | 12.9 | 41.3 | 8.5 | 10.5 | 10.9 |
| 2500 | M1 TabPFN v2 | skip | 12.1 | 40.5 | 8.4 | 8.8 | 9.9 |
| 5000 | B2 CAMS+hour bias | skip | skip | 55.0 | 44.0 | 54.6 | 24.2 |
| 5000 | B4 Ridge | skip | skip | 43.3 | 16.9 | 17.9 | 11.7 |
| 5000 | B5 HistGBR | skip | skip | 41.8 | 9.0 | 66.7 | 10.2 |
| 5000 | M1 TabPFN v2 | skip | skip | 39.9 | 10.7 | 8.9 | 8.2 |
| 10000 | B2 CAMS+hour bias | skip | skip | skip | skip | skip | 32.9 |
| 10000 | B4 Ridge | skip | skip | skip | skip | skip | 14.0 |
| 10000 | B5 HistGBR | skip | skip | skip | skip | skip | 9.0 |
| ref | B0 raw CAMS | 13.4 | 15.7 | 83.2 | 13.3 | 11.8 | 12.3 |

### Per-fold median ρ

| N | Model | F1 | F2 | F3 | F4 | F5 | F6 |
|---|---|---|---|---|---|---|---|
| 100 | B2 CAMS+hour bias | 0.306 | 0.549 | 0.535 | 0.361 | 0.276 | 0.610 |
| 100 | B4 Ridge | 0.196 | 0.429 | 0.223 | 0.626 | 0.411 | -0.033 |
| 100 | B5 HistGBR | 0.244 | 0.500 | 0.533 | 0.605 | 0.147 | 0.069 |
| 100 | M1 TabPFN v2 | 0.363 | 0.551 | 0.357 | 0.698 | 0.204 | -0.272 |
| 250 | B2 CAMS+hour bias | 0.333 | 0.536 | 0.550 | 0.459 | 0.380 | 0.729 |
| 250 | B4 Ridge | 0.188 | 0.513 | 0.464 | 0.683 | 0.407 | 0.567 |
| 250 | B5 HistGBR | 0.229 | 0.460 | 0.559 | 0.612 | 0.291 | 0.262 |
| 250 | M1 TabPFN v2 | 0.288 | 0.647 | 0.546 | 0.659 | 0.436 | 0.107 |
| 500 | B2 CAMS+hour bias | skip | 0.515 | 0.580 | 0.466 | 0.523 | 0.691 |
| 500 | B4 Ridge | skip | 0.537 | 0.519 | 0.489 | 0.373 | 0.725 |
| 500 | B5 HistGBR | skip | 0.516 | 0.487 | 0.602 | 0.357 | 0.249 |
| 500 | M1 TabPFN v2 | skip | 0.608 | 0.625 | 0.596 | 0.160 | 0.165 |
| 1000 | B2 CAMS+hour bias | skip | 0.540 | 0.609 | 0.498 | 0.440 | 0.586 |
| 1000 | B4 Ridge | skip | 0.377 | 0.558 | 0.570 | 0.187 | 0.655 |
| 1000 | B5 HistGBR | skip | 0.348 | 0.549 | 0.651 | 0.361 | 0.297 |
| 1000 | M1 TabPFN v2 | skip | 0.549 | 0.689 | 0.638 | 0.438 | 0.408 |
| 2500 | B2 CAMS+hour bias | skip | 0.634 | 0.665 | 0.386 | 0.496 | 0.535 |
| 2500 | B4 Ridge | skip | 0.471 | 0.597 | 0.440 | 0.176 | 0.581 |
| 2500 | B5 HistGBR | skip | 0.385 | 0.604 | 0.635 | 0.290 | 0.372 |
| 2500 | M1 TabPFN v2 | skip | 0.668 | 0.653 | 0.667 | 0.490 | 0.603 |
| 5000 | B2 CAMS+hour bias | skip | skip | 0.616 | 0.405 | 0.342 | 0.542 |
| 5000 | B4 Ridge | skip | skip | 0.622 | 0.629 | 0.300 | 0.637 |
| 5000 | B5 HistGBR | skip | skip | 0.589 | 0.659 | 0.345 | 0.574 |
| 5000 | M1 TabPFN v2 | skip | skip | 0.687 | 0.483 | 0.504 | 0.687 |
| 10000 | B2 CAMS+hour bias | skip | skip | skip | skip | skip | 0.610 |
| 10000 | B4 Ridge | skip | skip | skip | skip | skip | 0.604 |
| 10000 | B5 HistGBR | skip | skip | skip | skip | skip | 0.622 |
| ref | B0 raw CAMS | 0.238 | 0.674 | 0.604 | 0.281 | 0.235 | 0.602 |

### Per-fold hit %

| N | Model | F1 | F2 | F3 | F4 | F5 | F6 |
|---|---|---|---|---|---|---|---|
| 100 | B2 CAMS+hour bias | 23 | 43 | 59 | 37 | 43 | 57 |
| 100 | B4 Ridge | 35 | 43 | 37 | 43 | 50 | 17 |
| 100 | B5 HistGBR | 31 | 20 | 56 | 70 | 13 | 10 |
| 100 | M1 TabPFN v2 | 27 | 57 | 44 | 60 | 33 | 7 |
| 250 | B2 CAMS+hour bias | 31 | 37 | 63 | 43 | 43 | 70 |
| 250 | B4 Ridge | 12 | 27 | 22 | 63 | 47 | 43 |
| 250 | B5 HistGBR | 31 | 30 | 63 | 53 | 40 | 47 |
| 250 | M1 TabPFN v2 | 35 | 43 | 33 | 53 | 47 | 27 |
| 500 | B2 CAMS+hour bias | skip | 27 | 74 | 50 | 43 | 60 |
| 500 | B4 Ridge | skip | 40 | 15 | 53 | 40 | 63 |
| 500 | B5 HistGBR | skip | 30 | 33 | 40 | 43 | 40 |
| 500 | M1 TabPFN v2 | skip | 37 | 52 | 43 | 43 | 23 |
| 1000 | B2 CAMS+hour bias | skip | 27 | 74 | 47 | 47 | 70 |
| 1000 | B4 Ridge | skip | 33 | 30 | 53 | 47 | 60 |
| 1000 | B5 HistGBR | skip | 23 | 48 | 43 | 40 | 33 |
| 1000 | M1 TabPFN v2 | skip | 47 | 70 | 47 | 47 | 40 |
| 2500 | B2 CAMS+hour bias | skip | 30 | 67 | 50 | 47 | 50 |
| 2500 | B4 Ridge | skip | 33 | 37 | 47 | 53 | 53 |
| 2500 | B5 HistGBR | skip | 40 | 52 | 43 | 47 | 43 |
| 2500 | M1 TabPFN v2 | skip | 50 | 70 | 50 | 53 | 50 |
| 5000 | B2 CAMS+hour bias | skip | skip | 67 | 50 | 43 | 47 |
| 5000 | B4 Ridge | skip | skip | 67 | 47 | 17 | 37 |
| 5000 | B5 HistGBR | skip | skip | 48 | 50 | 43 | 53 |
| 5000 | M1 TabPFN v2 | skip | skip | 63 | 50 | 50 | 60 |
| 10000 | B2 CAMS+hour bias | skip | skip | skip | skip | skip | 57 |
| 10000 | B4 Ridge | skip | skip | skip | skip | skip | 37 |
| 10000 | B5 HistGBR | skip | skip | skip | skip | skip | 50 |
| ref | B0 raw CAMS | 35 | 47 | 37 | 37 | 37 | 63 |

Legend: `skip` = fewer than N valid rows before the window; `·` = not run / not completed.

### Paired per-fold differences (TabPFN − other; negative MAE diff / positive ρ diff = TabPFN better)

| N | vs | folds | mean ΔMAE | TabPFN better on MAE | mean Δρ | TabPFN better on ρ |
|---|---|---|---|---|---|---|
| 100 | B2 CAMS+hour bias | 6 | +0.54 | 4/6 | -0.123 | 3/6 |
| 100 | B4 Ridge | 6 | -301.16 | 6/6 | +0.008 | 4/6 |
| 100 | B5 HistGBR | 6 | +1.44 | 3/6 | -0.033 | 4/6 |
| 250 | B2 CAMS+hour bias | 6 | +0.23 | 4/6 | -0.051 | 3/6 |
| 250 | B4 Ridge | 6 | -55.76 | 6/6 | -0.023 | 4/6 |
| 250 | B5 HistGBR | 6 | -0.47 | 4/6 | +0.045 | 4/6 |
| 500 | B2 CAMS+hour bias | 5 | -3.47 | 4/5 | -0.124 | 3/5 |
| 500 | B4 Ridge | 5 | -34.64 | 5/5 | -0.098 | 3/5 |
| 500 | B5 HistGBR | 5 | +0.35 | 2/5 | -0.011 | 2/5 |
| 1000 | B2 CAMS+hour bias | 5 | -6.96 | 5/5 | +0.010 | 3/5 |
| 1000 | B4 Ridge | 5 | -33.30 | 4/5 | +0.075 | 4/5 |
| 1000 | B5 HistGBR | 5 | -0.04 | 3/5 | +0.103 | 4/5 |
| 2500 | B2 CAMS+hour bias | 5 | -14.20 | 5/5 | +0.073 | 3/5 |
| 2500 | B4 Ridge | 5 | -3.15 | 4/5 | +0.163 | 5/5 |
| 2500 | B5 HistGBR | 5 | -0.85 | 5/5 | +0.159 | 5/5 |
| 5000 | B2 CAMS+hour bias | 4 | -27.51 | 4/4 | +0.114 | 4/4 |
| 5000 | B4 Ridge | 4 | -5.49 | 4/4 | +0.043 | 3/4 |
| 5000 | B5 HistGBR | 4 | -14.99 | 3/4 | +0.049 | 3/4 |

### Pre-declared rules applied

| N | folds | TabPFN wins on MAE (majority of folds vs every other trained model)? | TabPFN wins on ρ? |
|---|---|---|---|
| 100 | 6 | no | no |
| 250 | 6 | YES | no |
| 500 | 5 | no | no |
| 1000 | 5 | YES | YES |
| 2500 | 5 | YES | YES |
| 5000 | 4 | YES | YES |

Usable = mean MAE (over the folds available at N) below B0 raw CAMS's mean MAE over the same folds:

| Model | 100 | 250 | 500 | 1000 | 2500 | 5000 | 10000 |
|---|---|---|---|---|---|---|---|
| B2 CAMS+hour bias | yes | yes | yes | yes | no | no | no |
| B4 Ridge | no | no | no | no | yes | yes | no |
| B5 HistGBR | yes | yes | yes | yes | yes | no | yes |
| M1 TabPFN v2 | yes | yes | yes | yes | yes | yes | · |

Smallest N at which each model is usable: B2 CAMS+hour bias: 100; B4 Ridge: 2500; B5 HistGBR: 100; M1 TabPFN v2: 100

### Wall-clock time per (model, N), mean over folds (seconds: fit / predict on ~700 eval rows)

| N | B2 CAMS+hour bias | B4 Ridge | B5 HistGBR | M1 TabPFN v2 |
|---|---|---|---|---|
| 100 | 0.0 / 0.0 | 0.0 / 0.0 | 0.1 / 0.0 | 5.5 / 25.2 |
| 250 | 0.0 / 0.0 | 0.0 / 0.0 | 0.3 / 0.0 | 24.4 / 55.4 |
| 500 | 0.0 / 0.0 | 0.0 / 0.0 | 0.5 / 0.0 | 52.1 / 62.9 |
| 1000 | 0.0 / 0.0 | 0.0 / 0.0 | 0.9 / 0.0 | 115.6 / 80.5 |
| 2500 | 0.0 / 0.0 | 0.0 / 0.0 | 0.7 / 0.0 | 439.8 / 120.7 |
| 5000 | 0.0 / 0.0 | 0.0 / 0.0 | 0.3 / 0.0 | 798.6 / 105.1 |
| 10000 | 0.0 / 0.0 | 0.0 / 0.0 | 0.5 / 0.0 | — |

### Skipped and missing cells

- N=500: skipped (insufficient history before window) in F1
- N=1000: skipped (insufficient history before window) in F1
- N=2500: skipped (insufficient history before window) in F1
- N=5000: skipped (insufficient history before window) in F1, F2
- N=10000: skipped (insufficient history before window) in F1, F2, F3, F4, F5
- Not run (time budget): F6/N=10000/M1 TabPFN v2
- Missing for other reasons: none

### Cross-sensor transfer: train at sensor 4554236 (N=2500), evaluate at sensor 4565419, no retraining

**Transfer (trained on 4554236)**, folds F2, F3, F4, F6

| Model | MAE | RMSE | median ρ | hit % |
|---|---|---|---|---|
| B0 raw CAMS | 27.5 ± 28.3 | 33.9 ± 33.4 | 0.570 ± 0.107 | 43 ± 15 |
| B2 CAMS+hour bias | 32.5 ± 24.7 | 37.4 ± 24.2 | 0.604 ± 0.127 | 47 ± 5 |
| B4 Ridge | 18.2 ± 11.6 | 23.8 ± 15.2 | 0.568 ± 0.054 | 47 ± 14 |
| B5 HistGBR | 17.5 ± 12.8 | 22.6 ± 16.5 | 0.521 ± 0.040 | 43 ± 5 |
| M1 TabPFN v2 | 16.8 ± 12.7 | 21.6 ± 16.0 | 0.661 ± 0.033 | 56 ± 8 |

**Native reference (trained on 4565419's own preceding rows)**, folds F3, F4, F6

| Model | MAE | RMSE | median ρ | hit % |
|---|---|---|---|---|
| B0 raw CAMS | 31.8 ± 33.1 | 38.9 ± 39.0 | 0.551 ± 0.123 | 40 ± 16 |
| B2 CAMS+hour bias | 39.7 ± 13.8 | 45.3 ± 12.9 | 0.574 ± 0.142 | 43 ± 9 |
| B4 Ridge | 24.8 ± 12.1 | 31.5 ± 16.7 | 0.493 ± 0.131 | 33 ± 6 |
| B5 HistGBR | 20.4 ± 16.2 | 26.6 ± 21.7 | 0.468 ± 0.139 | 37 ± 14 |

<!-- READING -->

# Reading the results

## Headline (negative at the small end, positive in the middle)

**TabPFN v2 does NOT win at the smallest training sizes in this experiment.** At N = 100–500 hours it is statistically
indistinguishable from untuned HistGBR on MAE (19.7 vs 18.3 at N=100; 17.9 vs 17.5 at N=500), and on the product metric
(within-day hour ranking) it is *worse* than the one-line baseline "CAMS + hour-of-day bias" (median ρ 0.317 vs 0.439 at N=100;
0.431 vs 0.555 at N=500) and even than raw CAMS at N=100. At N=100 its ranking is also the most erratic (ρ ± 0.336 across folds; ρ = −0.27 in F6).
The "TabPFN is best on tiny tabular data" claim is therefore **not supported here for N ≤ 500**.

**From about N = 1,000–2,500 hours (roughly 6 weeks to 3.5 months of a new sensor's data) TabPFN becomes the best, or tied-best, model.**
- Ranking: median ρ 0.544 (N=1000), 0.616 (N=2500), 0.590 (N=5000), beating HistGBR in 4/5, 5/5, 3/4 folds and Ridge in 4/5, 5/5, 3/4 folds. Against the B2 hour-bias baseline the ranking edge is small and not consistent (+0.010 at N=1000, 3/5 folds; +0.073 at N=2500, 3/5 folds; +0.114 at N=5000, 4/4 folds).
- MAE: lowest mean at N=2500 (16.0) and N=5000 (16.9). The margin over HistGBR is under 1 µg/m³ at N=1000–2500 (−0.04, −0.85; better in 3/5 and 5/5 folds); the large-looking margin at N=5000 (−15.0 vs HistGBR) is driven by one fold (F5, where HistGBR scores 66.7). TabPFN's MAE advantage over B2 and Ridge is large and consistent from N=1000 on (better than B2 in 5/5, 5/5, 4/4 folds).
- Top-2h-window hit rate follows the same pattern: TabPFN 50% / 55% / 56% at N=1000 / 2500 / 5000 vs 49–53% for B2 and 38–49% for the others; the differences are within the fold-to-fold spread.

**Crossover point:** by the pre-declared rule (lower MAE than every other trained model in a majority of folds, paired) TabPFN "wins" at N = 250 and N ≥ 1000, but at N = 250 the margins are a fraction of a µg/m³ (mean ΔMAE +0.23 vs B2, −0.47 vs HistGBR) so we do not call that a real win. The honest reading is that the crossover to a *consistent* advantage lies between N ≈ 1,000 and 2,500. The earlier evaluation (TEST month, ~10,000 training rows) also had TabPFN best, so we found no sign that it degrades at large N, but this experiment did **not** test it at N = 10,000 (see limitations).

## Other readings

- **Usability.** By the pre-declared rule (mean MAE below raw CAMS over the same folds) TabPFN, HistGBR and B2 are all "usable" from N = 100, and Ridge only from N = 2,500 (it is wildly unstable below that: MAE 321 ± 707 at N=100, 52 at N=500, with 26 features and few rows). This rule is lenient: raw CAMS's mean MAE is dominated by F3, the smog-season fold (MAE 83 vs 12–16 in the other five folds). Outside F3, a model trained on 100 hours is a toss-up with raw CAMS on MAE (e.g. F5: raw CAMS 11.8, TabPFN 14.6). The practical value of a correction at small N is mainly in smog months.
- **Seasonal sensitivity.** F3 (Jan 2026, smog tail) has MAE 40–55 for every trained model and 83 for raw CAMS; every fold-mean in the MAE tables is pulled by it. Paired per-fold differences are the right way to read this experiment.
- **Latency / cost (CPU laptop, ~700 eval rows).** TabPFN fit+predict averages about 30 s at N=100, 80 s at 250, 115 s at 500, 3 min at 1,000, 9 min at 2,500 and 15 min at 5,000 (single cells ranged from 12 to 22 min at N=5000), against well under 1 s for B2, Ridge and HistGBR. The cost is paid at fit time under `fit_with_cache` and grows faster than linearly with N. For a new sensor with a few hundred hours, TabPFN buys no accuracy and costs 30–120 s; at 1,000–2,500 hours it buys ranking quality at a cost of 3–9 minutes per refit.
- **Cross-sensor transfer (sensor 4554236 → sensor 4565419, N=2,500, no retraining, folds F2, F3, F4, F6).** TabPFN: MAE 16.8, median ρ 0.661, top-window hit 56%; HistGBR 17.5 / 0.521 / 43%; Ridge 18.2 / 0.568 / 47%; B2 32.5 / 0.604 / 47%; raw CAMS 27.5 / 0.570 / 43%. So a correction learned at one sensor carries over to a sensor 5 km away: all trained models beat raw CAMS on MAE except B2, and TabPFN has the best ranking. On the three folds where a native reference exists (F3, F4, F6; only for the non-TabPFN models), transfer was *not worse* than training on the target sensor's own preceding 2,500 rows (MAE: Ridge 20.2 vs 24.8; HistGBR 19.4 vs 20.4; B2 38.1 vs 39.7). We do not know why (the target sensor has outages, so its "preceding 2,500 rows" may span a different calendar period; this was not investigated). A TabPFN native reference was **not run** (time budget), and both sensors share identical CAMS/weather inputs, so this tests the correction mapping, not different local meteorology.

# Limitations

- **Small experiment.** 6 folds (4–5 for most cells, 1 for N=10,000), one city, two sensors, one random seed for TabPFN/HistGBR. Fold-to-fold standard deviations are as large as the means, no confidence intervals are computed, and "majority of folds" is a crude decision rule. Differences below ~1–2 µg/m³ or ~0.05 in ρ should be read as ties.
- **The fold set changes with N** (later folds have more history), so the headline curves mix N with season and fold difficulty; N=5000 is F3–F6 only, N=10,000 is F6 only. Use the per-fold and paired tables.
- **Recency windows reach back across seasons.** At N=5000, F5 (a June window) trains on data reaching back into winter; the large HistGBR (66.7) and B2 (54.6) errors there are probably this seasonal shift, which TabPFN weathers better (8.9). This explanation is a hypothesis, not tested.
- **N = 10,000 was not evaluated for TabPFN** (budget; only F6 exists for that size, and only the baselines ran). The "worst case at 10,000" question is therefore not re-tested here.
- **Inputs are archive CAMS/weather values, not live day-ahead forecasts**, and the target is an uncalibrated low-cost sensor; absolute errors are optimistic for real-time use.
- **No tuning of anything**, as pre-declared; Ridge's small-N failure and HistGBR's defaults are therefore not representative of what a tuned baseline would achieve.
- **Process disclosures.**
  1. The F6 window coincides with the DEV split of the earlier evaluation; the spent TEST month was not used.
  2. A bug in my compute-budget estimator (quadratic extrapolation from the N=500 timings) wrongly skipped all N=5000 and N=10,000 TabPFN fits at 84 minutes, when ~91 minutes were left. I found it from the logs, fixed the estimator, cleared those five "not run" entries and resumed within the original 3-hour box. No result informed this change and the protocol was not altered. N=5000 then completed on all four eligible folds; N=10,000 was then skipped for genuine budget reasons. The same estimator also initially skipped the F6 cross-sensor TabPFN cell, which I ran afterwards (about 6 more minutes, still inside the box).
  3. I looked at interim aggregate tables once, at about 40 minutes (N ≤ 1000 complete), and at baseline-only numbers in a dry run before launch. Nothing in the protocol was changed afterwards.
  4. Protocol dates for F2 and F3 were nudged by a few days before any model ran, to make N=2500 and N=5000 reachable.
  5. TabPFN wall-clock times may include contention from other processes on the same laptop; this was not controlled.
- **Cross-sensor coverage.** F1 (not enough history at sensor 4554236 for N=2,500) and F5 (sensor 4565419 was offline for most of that window) have no transfer cell; TabPFN native-reference cells were not run.

