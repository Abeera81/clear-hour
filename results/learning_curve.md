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

_Results pending: the run has not started when this protocol was committed._
