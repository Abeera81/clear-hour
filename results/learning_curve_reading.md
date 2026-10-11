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
