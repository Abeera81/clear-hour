# Score — forecast for 2026-10-11

Forecast file generated 2026-10-11T01:51:15+00:00 UTC (stage: stage2 (all three models)). Truth: OpenAQ sensor 4554236 (uncalibrated low-cost AirGradient, CC BY 4.0, The Urban Unit), hourly means, Asia/Karachi. Measured hours: **24/24**.

> Late entry: TabPFN committed at 06:51 (Asia/Karachi, 2026-10-11). Hours before that time had already occurred and are NOT pre-registered. B0 and B2 were committed at 06:10:46.

## Full day (all 24 hours)

Hours 00:00-23:59, 24 measured. Actual mean **45.4** µg/m³; best possible 2h window 20.9 (17:00); worst 79.2 (00:00). 'Cleanest set' = the 6 lowest measured hours in this view: 17h, 18h, 19h, 20h, 21h, 22h.

| Model | MAE | Bias | Spearman | Chosen cleanest 2h | Actual PM2.5 there | vs mean | Inside cleanest set? | Chosen dirtiest 2h | Actual there |
|---|---|---|---|---|---|---|---|---|---|
| M1 TabPFN v2 | 21.9 | +14.6 | -0.369 | 15:00-17:00 | 29.8 | -15.6 | no | 22:00-00:00 | 30.7 |
| B0 raw CAMS | 21.9 | -3.5 | -0.512 | 05:00-07:00 | 73.7 | +28.3 | no | 22:00-00:00 | 30.7 |
| B2 CAMS+hour bias | 25.3 | +18.8 | -0.409 | 15:00-17:00 | 29.8 | -15.6 | no | 22:00-00:00 | 30.7 |

## Hours >= 07:00 only (late-entry view; windows re-derived from each model's own predictions in this range)

Hours 07:00-23:59, 17 measured. Actual mean **35.7** µg/m³; best possible 2h window 20.9 (17:00); worst 50.2 (11:00). 'Cleanest set' = the 4 lowest measured hours in this view: 17h, 18h, 19h, 20h.

| Model | MAE | Bias | Spearman | Chosen cleanest 2h | Actual PM2.5 there | vs mean | Inside cleanest set? | Chosen dirtiest 2h | Actual there |
|---|---|---|---|---|---|---|---|---|---|
| M1 TabPFN v2 | 25.6 | +25.6 | -0.483 | 15:00-17:00 | 29.8 | -5.9 | no | 22:00-00:00 | 30.7 |
| B0 raw CAMS | 18.1 | +7.8 | -0.701 | 09:00-11:00 | 47.8 | +12.1 | no | 22:00-00:00 | 30.7 |
| B2 CAMS+hour bias | 30.9 | +30.9 | -0.153 | 15:00-17:00 | 29.8 | -5.9 | no | 22:00-00:00 | 30.7 |

Notes: MAE/Bias in µg/m³ (pred − actual); Spearman over measured hours in the view. 'Inside cleanest set' needs both hours of the 2h window among the view's lowest measured hours. One day is one sample; do not read skill into a single result.
