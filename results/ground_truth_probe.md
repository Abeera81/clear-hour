# Clear Hour — ground-truth probe (OpenAQ v3)

Centre lat 33.6, lon 73.05; bbox 72.51,33.15,73.59,34.05 (~50 km). Run 2026-10-10 17:33 UTC by `scripts/ground_truth_probe.py`. Aggregates only.

## 1) Monitoring locations within ~50 km

OpenAQ returns **55** locations; **2** flagged reference-grade (`isMonitor=true`), the rest low-cost sensors.

| id | Name | Lat, Lon | km | Grade | Provider | Parameters | First (UTC) | Last (UTC) |
|---|---|---|---|---|---|---|---|---|
| 8634 | US Diplomatic Post: Islamabad | 33.7235, 73.1182 | 15.1 | reference | StateAir Islamabad | pm25 | 2019-05-22 | 2025-03-04 |
| 233470 | Islamabad | 33.7256, 73.1160 | 15.2 | reference | AirNow | pm25 | 2021-08-26 | 2026-02-16 |
| 4565932 | WASA Head Office 1 | 33.6023, 73.0560 | 0.6 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-05-30 | 2026-10-10 |
| 4567932 | PHA Head Office | 33.6055, 73.0611 | 1.2 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-05-30 | 2026-10-10 |
| 6135474 | PHA Head Office | 33.6055, 73.0611 | 1.2 | low-cost | Hawanama | pm25 | 2025-11-20 | 2026-10-10 |
| 6135352 | Westridge1 | 33.6110, 73.0269 | 2.5 | low-cost | Hawanama | pm25 | 2025-11-18 | 2026-04-15 |
| 4884063 | Govt. Graduate College, Asghar Mall, | 33.6291, 73.0559 | 3.3 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-06-28 | 2026-10-10 |
| 4616262 | District Health Authority | 33.6333, 73.0489 | 3.7 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-06-04 | 2026-10-08 |
| 4567363 | Public Health Engineering | 33.6336, 73.0614 | 3.9 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-05-30 | 2026-09-27 |
| 4566426 | Punjab Food Authority | 33.6305, 73.0730 | 4.0 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-05-30 | 2026-10-10 |
| 6135510 | Punjab Food Authority | 33.6305, 73.0730 | 4.0 | low-cost | Hawanama | pm25 | 2025-11-20 | 2026-10-10 |
| 6135470 | NASTP | 33.6079, 73.0975 | 4.5 | low-cost | Hawanama | pm25 | 2025-11-19 | 2026-10-05 |
| 4917341 | NASTP | 33.6079, 73.0975 | 4.5 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-07-02 | 2026-10-05 |
| 6135529 | WASA 2 (Sufaid tanki) | 33.6386, 73.0694 | 4.7 | low-cost | Hawanama | pm25 | 2025-11-25 | 2026-10-10 |
| 4579733 | WASA 2 (Sufaid tanki) | 33.6386, 73.0694 | 4.7 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-05-31 | 2026-10-10 |
| 6135514 | Fair Finance Pakistan Islamabad | 33.6347, 73.0169 | 4.9 | low-cost | Hawanama | pm25 | 2025-11-18 | 2026-04-15 |
| 4565419 | Social Welfare Department | 33.6279, 73.0925 | 5.0 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-05-30 | 2026-10-10 |
| 4296966 | Buraq integrated solutions | 33.6432, 73.0681 | 5.1 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-05-06 | 2025-05-17 |
| 5371016 | DC office | 33.6434, 73.0682 | 5.1 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-08-09 | 2025-08-25 |
| 5325356 | DC Office Sialkot | 33.6434, 73.0683 | 5.1 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-08-05 | 2026-10-10 |
| 4554236 | Rawalpindi Women University | 33.6452, 73.0646 | 5.2 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-05-29 | 2026-10-10 |
| 4556719 | Wasa 3, OHR Office | 33.6510, 73.0789 | 6.3 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-05-29 | 2026-10-10 |
| 6135332 | Islamabad H11 A | 33.6457, 73.0050 | 6.6 | low-cost | Hawanama | pm25 | 2025-11-18 | 2026-10-10 |
| 6135359 | Rawalpindi A GT Road | 33.5482, 73.1017 | 7.5 | low-cost | Hawanama | pm25 | 2025-11-18 | 2026-10-10 |
| 6135310 | Bahria Town Phase 2 | 33.5541, 73.1214 | 8.4 | low-cost | Hawanama | pm25 | 2025-11-18 | 2026-10-10 |
| 6135307 | Dr Abuzar - Bahria Town, Phase 5 | 33.5613, 73.1308 | 8.6 | low-cost | Hawanama | pm25 | 2025-11-18 | 2026-10-10 |
| 4567364 | Conservator of Forest, North zone | 33.5406, 73.1169 | 9.1 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-05-30 | 2026-10-10 |
| 6509912 | Gulberg Greens Isb | 33.6099, 73.1633 | 10.6 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2026-08-27 | 2026-10-10 |
| 4608422 | Park Road F-8/1 Sector Islamabad | 33.7103, 73.0313 | 12.4 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-06-03 | 2026-10-10 |
| 4568424 | E11/4 Sector Islamabad | 33.6990, 72.9819 | 12.7 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-05-30 | 2026-10-10 |
| 6135338 | F7-2, Street 20 | 33.7168, 73.0441 | 13.0 | low-cost | Hawanama | pm25 | 2025-11-18 | 2026-04-17 |
| 4515644 | F-7, Islamabad | 33.7213, 73.0561 | 13.5 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-05-24 | 2026-10-05 |
| 6135304 | Street 8, Sector F-7/3, Islamabad | 33.7233, 73.0637 | 13.8 | low-cost | Hawanama | pm25 | 2025-11-18 | 2026-10-10 |
| 6135345 | house street22 e7 | 33.7318, 73.0481 | 14.7 | low-cost | Hawanama | pm25 | 2025-11-18 | 2026-07-10 |
| 6135335 | Street # 1, F-6/3 | 33.7306, 73.0812 | 14.8 | low-cost | Hawanama | pm25 | 2025-11-18 | 2026-10-10 |
| 6509913 | Central | 33.6389, 73.2039 | 14.9 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2026-08-27 | 2026-10-08 |
| 6505270 | North | 33.6439, 73.2023 | 14.9 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2026-08-24 | 2026-09-12 |
| 6135297 | Islamabad Station | 33.7256, 73.1160 | 15.2 | low-cost | Hawanama | pm25 | 2025-11-18 | 2026-02-16 |
| 6135327 | Mughal Village, Islamabad (Zone 5) | 33.5555, 73.2535 | 19.5 | low-cost | Hawanama | pm25 | 2025-11-18 | 2026-10-10 |
| 6135441 | Device 1, Suraj Gali | 33.8424, 72.9188 | 29.6 | low-cost | Hawanama | pm25 | 2025-11-19 | 2025-11-20 |
| 6135300 | Dewan Cement Hattar 2 | 33.8560, 72.8621 | 33.4 | low-cost | Hawanama | pm25 | 2025-11-18 | 2026-02-05 |
| 6135317 | Dewan Cement Hattar | 33.8560, 72.8621 | 33.4 | low-cost | Hawanama | pm25 | 2025-11-18 | 2026-02-05 |
| 6135341 | Dewan Cement Hattar 3 | 33.8560, 72.8621 | 33.4 | low-cost | Hawanama | pm25 | 2025-11-18 | 2026-02-05 |
| 6135362 | Dewan Cement Hattar 4 | 33.8560, 72.8621 | 33.4 | low-cost | Hawanama | pm25 | 2025-11-18 | 2026-02-05 |
| 6135358 | Dewan Cement Hattar 5 | 33.8561, 72.8622 | 33.4 | low-cost | Hawanama | pm25 | 2025-11-18 | 2026-02-05 |
| 6135284 | DCL Hattar | 33.8564, 72.8622 | 33.4 | low-cost | Hawanama | pm25 | 2025-11-18 | 2026-07-11 |
| 6131330 | Govt Higher Secondary School Karore Kotli Sattian | 33.7477, 73.4074 | 36.9 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-11-15 | 2026-10-10 |
| 6130996 | Govt Girls High School Samli Tajjal Murree | 33.8526, 73.3205 | 37.6 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-11-15 | 2026-10-07 |
| 6135322 | Chakbeli Khan, Rawalpindi | 33.2361, 72.9137 | 42.4 | low-cost | Hawanama | pm25 | 2025-11-18 | 2026-10-10 |
| 6130288 | Govt Girls High School, Murree City | 33.9075, 73.3923 | 46.6 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-11-14 | 2026-10-10 |
| 4618315 | DC Office Murree | 33.9066, 73.3980 | 46.9 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-06-04 | 2025-11-20 |
| 6137242 | Deputy Commissioner Office, Murree | 33.9045, 73.4021 | 47.0 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-11-20 | 2026-10-10 |
| 6131254 | Govt Sufi Abdul Aziz High School Kotli Sattian | 33.7984, 73.5195 | 48.7 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-11-15 | 2026-10-10 |
| 6135494 | WWF-Pakistan Nathiagali | 34.0233, 73.2595 | 50.9 | low-cost | Hawanama | pm25 | 2025-11-21 | 2026-06-15 |
| 6130291 | Govt Boys High School Rawat Murree | 33.9590, 73.4567 | 54.8 | low-cost | AirGradient | pm1, pm25, relativehumidity, temperature, um003 | 2025-11-14 | 2026-10-10 |

## 2) Hourly PM2.5 coverage

- StateAir vs AirNow feeds, 15949 common hours: mean |diff| 2.11 µg/m³ (same instrument, two feeds)

**US Diplomatic Post: Islamabad [8634, StateAir Islamabad]**

- Span (local, hour ending): 2019-05-23 03:00 → 2025-03-04 17:00
- Valid hours: **36912** of 50703 in span → **27.2% missing**
- Gaps > 24 h: **57**, totalling 10305 h

| Year | Valid hours |
|---|---|
| 2019 | 5042 |
| 2020 | 8224 |
| 2021 | 5299 |
| 2022 | 5292 |
| 2023 | 5090 |
| 2024 | 6492 |
| 2025 | 1473 |

Longest gaps:
- 2023-11-02 19:00:00 → 2024-03-19 01:00:00 (3295 h)
- 2021-07-13 16:00:00 → 2021-08-26 15:00:00 (1056 h)
- 2023-02-16 06:00:00 → 2023-03-19 05:00:00 (744 h)
- 2021-10-27 17:00:00 → 2021-11-18 02:00:00 (514 h)
- 2021-09-08 00:00:00 → 2021-09-23 18:00:00 (379 h)
- 2022-05-24 23:00:00 → 2022-06-07 07:00:00 (321 h)
- 2023-02-02 06:00:00 → 2023-02-14 05:00:00 (288 h)
- 2021-05-06 18:00:00 → 2021-05-18 12:00:00 (283 h)

**Islamabad [233470, AirNow]**

- Span (local, hour ending): 2021-08-26 20:00 → 2026-02-16 18:00
- Valid hours: **28912** of 39239 in span → **26.3% missing**
- Gaps > 24 h: **24**, totalling 9657 h

| Year | Valid hours |
|---|---|
| 2021 | 5 |
| 2022 | 4254 |
| 2023 | 7234 |
| 2024 | 8288 |
| 2025 | 8011 |
| 2026 | 1120 |

Longest gaps:
- 2022-01-25 23:00:00 → 2022-06-06 14:00:00 (3160 h)
- 2021-09-23 20:00:00 → 2021-11-30 06:00:00 (1619 h)
- 2021-11-30 19:00:00 → 2022-01-13 19:00:00 (1057 h)
- 2023-02-16 07:00:00 → 2023-03-19 06:00:00 (744 h)
- 2021-08-26 21:00:00 → 2021-09-23 18:00:00 (670 h)
- 2025-11-28 13:00:00 → 2025-12-14 06:00:00 (378 h)
- 2023-02-02 07:00:00 → 2023-02-14 06:00:00 (288 h)
- 2022-01-14 04:00:00 → 2022-01-25 21:00:00 (282 h)

**US Embassy Islamabad — merged StateAir+AirNow**

- Span (local, hour ending): 2019-05-23 03:00 → 2026-02-16 18:00
- Valid hours: **49875** of 59080 in span → **15.6% missing**
- Gaps > 24 h: **48**, totalling 6936 h

| Year | Valid hours |
|---|---|
| 2019 | 5042 |
| 2020 | 8224 |
| 2021 | 5301 |
| 2022 | 6616 |
| 2023 | 7267 |
| 2024 | 8294 |
| 2025 | 8011 |
| 2026 | 1120 |

Longest gaps:
- 2021-07-13 16:00:00 → 2021-08-26 15:00:00 (1056 h)
- 2023-02-16 07:00:00 → 2023-03-19 05:00:00 (743 h)
- 2021-10-27 17:00:00 → 2021-11-18 02:00:00 (514 h)
- 2021-09-08 00:00:00 → 2021-09-23 18:00:00 (379 h)
- 2025-11-28 13:00:00 → 2025-12-14 06:00:00 (378 h)
- 2022-05-24 23:00:00 → 2022-06-06 14:00:00 (304 h)
- 2023-02-02 07:00:00 → 2023-02-14 05:00:00 (287 h)
- 2021-05-06 18:00:00 → 2021-05-18 12:00:00 (283 h)

**Rawalpindi Women University [4554236, AirGradient, low-cost, 5.2 km]**

- Span (local, hour ending): 2025-05-29 12:00 → 2026-10-10 21:00
- Valid hours: **11691** of 11986 in span → **2.5% missing**
- Gaps > 24 h: **3**, totalling 85 h

| Year | Valid hours |
|---|---|
| 2025 | 4988 |
| 2026 | 6703 |

Longest gaps:
- 2025-11-12 09:00:00 → 2025-11-13 18:00:00 (34 h)
- 2025-08-12 08:00:00 → 2025-08-13 09:00:00 (26 h)
- 2025-06-13 18:00:00 → 2025-06-14 18:00:00 (25 h)

**Wasa 3, OHR Office [4556719, AirGradient, low-cost, 6.3 km]**

- Span (local, hour ending): 2025-05-29 17:00 → 2026-10-10 21:00
- Valid hours: **6018** of 11981 in span → **49.8% missing**
- Gaps > 24 h: **36**, totalling 4668 h

| Year | Valid hours |
|---|---|
| 2025 | 4232 |
| 2026 | 1786 |

Longest gaps:
- 2026-04-08 14:00:00 → 2026-07-29 02:00:00 (2677 h)
- 2026-07-29 04:00:00 → 2026-08-06 19:00:00 (208 h)
- 2026-03-18 11:00:00 → 2026-03-23 14:00:00 (124 h)
- 2026-08-06 23:00:00 → 2026-08-10 15:00:00 (89 h)
- 2025-06-05 00:00:00 → 2025-06-08 13:00:00 (86 h)
- 2025-10-03 21:00:00 → 2025-10-07 09:00:00 (85 h)
- 2026-03-14 02:00:00 → 2026-03-17 10:00:00 (81 h)
- 2025-07-31 20:00:00 → 2025-08-03 19:00:00 (72 h)

**Social Welfare Department [4565419, AirGradient, low-cost, 5.0 km]**

- Span (local, hour ending): 2025-05-30 11:00 → 2026-10-10 19:00
- Valid hours: **9101** of 11961 in span → **23.9% missing**
- Gaps > 24 h: **3**, totalling 2379 h

| Year | Valid hours |
|---|---|
| 2025 | 4783 |
| 2026 | 4318 |

Longest gaps:
- 2026-05-04 14:00:00 → 2026-07-23 11:00:00 (1918 h)
- 2026-07-23 13:00:00 → 2026-08-06 14:00:00 (338 h)
- 2025-08-01 10:00:00 → 2025-08-06 12:00:00 (123 h)

## 3) Recency — last 7 days

| Series | Hours in last 7 days (of 168) | Latest reading (local) | Age |
|---|---|---|---|
| US Diplomatic Post: Islamabad [8634, StateAir Islamabad] | 0 | 2025-03-04 17:00 | 14046 h |
| Islamabad [233470, AirNow] | 0 | 2026-02-16 18:00 | 5669 h |
| US Embassy Islamabad — merged StateAir+AirNow | 0 | 2026-02-16 18:00 | 5669 h |
| Rawalpindi Women University [4554236, AirGradient, low-cost, 5.2 km] | 167 | 2026-10-10 21:00 | 2 h |
| Wasa 3, OHR Office [4556719, AirGradient, low-cost, 6.3 km] | 45 | 2026-10-10 21:00 | 2 h |
| Social Welfare Department [4565419, AirGradient, low-cost, 5.0 km] | 129 | 2026-10-10 19:00 | 4 h |

Latest-reading endpoint (`/locations/{id}/latest`) for the embassy + chosen low-cost sites:

- 8634 US Diplomatic Post: Islamabad: 16.0 µg/m³ at 2025-03-04T17:00:00+05:00
- 233470 Islamabad: 62.0 µg/m³ at 2026-02-16T18:00:00+05:00
- 4554236 Rawalpindi Women University: 90.6 µg/m³ at 2026-10-10T22:00:00+05:00
- 4556719 Wasa 3, OHR Office: 99.8 µg/m³ at 2026-10-10T21:00:00+05:00
- 4565419 Social Welfare Department: 78.2 µg/m³ at 2026-10-10T19:00:00+05:00
- Current low-cost PM2.5 sites (last reading within 3 days, any distance ≤50 km): **31**; current reference-grade sites: **0**

## 4) CAMS (Open-Meteo, 33.6, 73.05) vs monitors — overlap

CAMS = instantaneous model value (local time); monitor = hourly mean, hour-ending, converted UTC→Asia/Karachi. CAMS artifact days 2022-12-14/15 excluded.

### CAMS vs US Embassy Islamabad — merged StateAir+AirNow

- Overlap: **27993 h** (2022-08-04 → 2026-02-16)
- Hourly Pearson r: **0.555**; Spearman: 0.426
- Daily-mean Pearson r: **0.625** (n=1202 days)
- Mean error (CAMS − monitor): **-18.9 µg/m³**; MAE **29.9**; monitor mean 57.5, CAMS mean 38.6
- Ratio monitor/CAMS (median of hourly ratios, CAMS>1): 1.28

Alignment sensitivity:

| Alignment | n | Pearson r |
|---|---|---|
| CAMS at hour end | 27993 | 0.555 |
| CAMS at hour start | 27992 | 0.517 |
| CAMS 1 h after end | 27994 | 0.554 |

- Within-day hour ranking (Spearman per day, days with ≥20 h, n=1143): median **0.43**, mean 0.35

Bias by hour of day (local, hour ending), µg/m³:

| Hour | n | Monitor mean | CAMS mean | Bias (CAMS−mon) | Bias Oct–Dec | Bias rest |
|---|---|---|---|---|---|---|
| 00 | 1161 | 57.0 | 49.3 | -7.8 | -23.5 | -1.5 |
| 01 | 1164 | 49.2 | 44.1 | -5.1 | -19.0 | +0.6 |
| 02 | 1168 | 45.8 | 39.6 | -6.2 | -19.9 | -0.6 |
| 03 | 1168 | 42.5 | 35.9 | -6.7 | -20.2 | -1.2 |
| 04 | 1168 | 40.8 | 32.9 | -7.9 | -20.4 | -2.8 |
| 05 | 1166 | 42.2 | 30.2 | -12.0 | -22.3 | -7.9 |
| 06 | 1177 | 41.8 | 29.4 | -12.4 | -23.4 | -8.0 |
| 07 | 1169 | 48.0 | 31.6 | -16.4 | -31.1 | -10.5 |
| 08 | 1171 | 64.8 | 34.6 | -30.2 | -61.9 | -17.3 |
| 09 | 1163 | 79.4 | 35.0 | -44.4 | -90.4 | -25.5 |
| 10 | 1168 | 56.3 | 33.8 | -22.5 | -43.7 | -13.8 |
| 11 | 1153 | 46.9 | 31.6 | -15.3 | -29.1 | -9.8 |
| 12 | 1165 | 49.4 | 30.9 | -18.5 | -32.3 | -12.9 |
| 13 | 1174 | 52.8 | 30.8 | -22.1 | -41.8 | -14.1 |
| 14 | 1170 | 52.4 | 30.8 | -21.6 | -44.0 | -12.5 |
| 15 | 1169 | 49.8 | 30.9 | -18.9 | -39.8 | -10.5 |
| 16 | 1168 | 48.0 | 31.9 | -16.0 | -32.9 | -9.2 |
| 17 | 1170 | 49.4 | 35.0 | -14.4 | -29.4 | -8.4 |
| 18 | 1164 | 62.4 | 42.4 | -20.0 | -51.5 | -7.2 |
| 19 | 1162 | 80.2 | 49.0 | -31.2 | -73.5 | -14.2 |
| 20 | 1168 | 88.1 | 53.3 | -34.8 | -70.9 | -20.1 |
| 21 | 1168 | 87.2 | 55.1 | -32.1 | -64.5 | -19.2 |
| 22 | 1163 | 78.2 | 55.5 | -22.7 | -47.1 | -12.9 |
| 23 | 1156 | 67.2 | 53.7 | -13.5 | -32.1 | -6.0 |

### CAMS vs Rawalpindi Women University [4554236, AirGradient, low-cost, 5.2 km]

- Overlap: **11669 h** (2025-05-29 → 2026-10-09)
- Hourly Pearson r: **0.527**; Spearman: 0.474
- Daily-mean Pearson r: **0.662** (n=499 days)
- Mean error (CAMS − monitor): **-22.3 µg/m³**; MAE **31.9**; monitor mean 62.1, CAMS mean 39.8
- Ratio monitor/CAMS (median of hourly ratios, CAMS>1): 1.28

Alignment sensitivity:

| Alignment | n | Pearson r |
|---|---|---|
| CAMS at hour end | 11669 | 0.527 |
| CAMS at hour start | 11670 | 0.540 |
| CAMS 1 h after end | 11668 | 0.498 |

- Within-day hour ranking (Spearman per day, days with ≥20 h, n=478): median **0.44**, mean 0.35

Bias by hour of day (local, hour ending), µg/m³:

| Hour | n | Monitor mean | CAMS mean | Bias (CAMS−mon) | Bias Oct–Dec | Bias rest |
|---|---|---|---|---|---|---|
| 00 | 488 | 73.0 | 54.3 | -18.6 | -70.9 | -5.4 |
| 01 | 488 | 71.0 | 48.7 | -22.3 | -76.7 | -8.3 |
| 02 | 488 | 68.5 | 43.3 | -25.1 | -77.7 | -11.6 |
| 03 | 487 | 62.8 | 38.9 | -23.9 | -74.0 | -11.0 |
| 04 | 487 | 58.5 | 35.1 | -23.5 | -71.9 | -11.1 |
| 05 | 487 | 56.6 | 33.8 | -22.8 | -68.8 | -11.0 |
| 06 | 489 | 55.8 | 32.0 | -23.8 | -69.1 | -12.1 |
| 07 | 489 | 57.1 | 33.5 | -23.5 | -65.4 | -12.9 |
| 08 | 487 | 61.0 | 34.5 | -26.5 | -68.3 | -15.8 |
| 09 | 483 | 63.7 | 33.3 | -30.5 | -75.9 | -19.2 |
| 10 | 483 | 63.7 | 31.4 | -32.3 | -79.9 | -20.5 |
| 11 | 482 | 63.1 | 29.3 | -33.7 | -89.7 | -20.2 |
| 12 | 482 | 63.7 | 29.1 | -34.6 | -101.3 | -18.5 |
| 13 | 485 | 59.6 | 28.9 | -30.7 | -94.9 | -15.0 |
| 14 | 484 | 53.7 | 28.8 | -25.0 | -78.0 | -12.2 |
| 15 | 485 | 49.0 | 28.8 | -20.2 | -65.8 | -8.7 |
| 16 | 481 | 45.5 | 29.8 | -15.7 | -53.9 | -6.2 |
| 17 | 483 | 46.7 | 33.7 | -12.9 | -48.4 | -4.1 |
| 18 | 482 | 51.6 | 41.5 | -10.1 | -48.1 | -0.7 |
| 19 | 489 | 62.9 | 49.9 | -13.1 | -67.6 | +0.9 |
| 20 | 488 | 71.8 | 55.9 | -15.9 | -73.7 | -1.0 |
| 21 | 490 | 77.1 | 59.1 | -18.0 | -75.8 | -3.1 |
| 22 | 490 | 77.6 | 60.5 | -17.2 | -70.9 | -3.4 |
| 23 | 492 | 75.2 | 59.0 | -16.3 | -68.5 | -2.9 |

### CAMS vs Wasa 3, OHR Office [4556719, AirGradient, low-cost, 6.3 km]

- Overlap: **6010 h** (2025-05-29 → 2026-10-09)
- Hourly Pearson r: **0.534**; Spearman: 0.446
- Daily-mean Pearson r: **0.621** (n=337 days)
- Mean error (CAMS − monitor): **-37.3 µg/m³**; MAE **44.6**; monitor mean 81.4, CAMS mean 44.0
- Ratio monitor/CAMS (median of hourly ratios, CAMS>1): 1.63

Alignment sensitivity:

| Alignment | n | Pearson r |
|---|---|---|
| CAMS at hour end | 6010 | 0.534 |
| CAMS at hour start | 6010 | 0.537 |
| CAMS 1 h after end | 6010 | 0.512 |

- Within-day hour ranking (Spearman per day, days with ≥20 h, n=182): median **0.43**, mean 0.37

Bias by hour of day (local, hour ending), µg/m³:

| Hour | n | Monitor mean | CAMS mean | Bias (CAMS−mon) | Bias Oct–Dec | Bias rest |
|---|---|---|---|---|---|---|
| 00 | 255 | 93.3 | 59.5 | -33.8 | -79.5 | -12.9 |
| 01 | 250 | 90.2 | 53.3 | -36.9 | -83.1 | -14.8 |
| 02 | 249 | 86.2 | 47.7 | -38.5 | -83.0 | -17.0 |
| 03 | 249 | 78.4 | 42.6 | -35.8 | -80.6 | -14.2 |
| 04 | 241 | 74.2 | 38.6 | -35.6 | -79.1 | -14.0 |
| 05 | 237 | 72.8 | 34.9 | -37.9 | -77.7 | -17.2 |
| 06 | 239 | 71.7 | 33.1 | -38.6 | -76.9 | -18.9 |
| 07 | 237 | 76.2 | 35.5 | -40.6 | -77.5 | -21.5 |
| 08 | 237 | 80.1 | 38.4 | -41.7 | -77.0 | -23.8 |
| 09 | 242 | 82.1 | 37.7 | -44.4 | -79.1 | -27.9 |
| 10 | 229 | 82.1 | 34.2 | -47.9 | -87.7 | -28.5 |
| 11 | 232 | 82.5 | 31.2 | -51.3 | -101.0 | -28.0 |
| 12 | 243 | 81.5 | 30.6 | -51.0 | -109.1 | -25.0 |
| 13 | 250 | 74.9 | 30.4 | -44.5 | -101.4 | -19.6 |
| 14 | 252 | 66.1 | 30.5 | -35.7 | -88.3 | -12.9 |
| 15 | 271 | 63.1 | 30.2 | -32.9 | -76.8 | -13.2 |
| 16 | 257 | 65.7 | 32.0 | -33.7 | -66.8 | -18.8 |
| 17 | 257 | 69.2 | 38.4 | -30.9 | -64.0 | -15.6 |
| 18 | 263 | 78.0 | 48.5 | -29.5 | -72.2 | -9.5 |
| 19 | 269 | 91.4 | 57.6 | -33.8 | -85.8 | -9.8 |
| 20 | 266 | 95.2 | 63.6 | -31.6 | -78.1 | -9.7 |
| 21 | 262 | 99.1 | 66.8 | -32.4 | -82.0 | -8.9 |
| 22 | 262 | 98.4 | 67.2 | -31.1 | -76.4 | -10.1 |
| 23 | 261 | 97.1 | 65.4 | -31.8 | -76.6 | -10.9 |

### CAMS vs Social Welfare Department [4565419, AirGradient, low-cost, 5.0 km]

- Overlap: **9082 h** (2025-05-30 → 2026-10-09)
- Hourly Pearson r: **0.564**; Spearman: 0.483
- Daily-mean Pearson r: **0.703** (n=402 days)
- Mean error (CAMS − monitor): **-23.7 µg/m³**; MAE **33.3**; monitor mean 64.8, CAMS mean 41.1
- Ratio monitor/CAMS (median of hourly ratios, CAMS>1): 1.36

Alignment sensitivity:

| Alignment | n | Pearson r |
|---|---|---|
| CAMS at hour end | 9082 | 0.564 |
| CAMS at hour start | 9083 | 0.580 |
| CAMS 1 h after end | 9081 | 0.530 |

- Within-day hour ranking (Spearman per day, days with ≥20 h, n=352): median **0.46**, mean 0.36

Bias by hour of day (local, hour ending), µg/m³:

| Hour | n | Monitor mean | CAMS mean | Bias (CAMS−mon) | Bias Oct–Dec | Bias rest |
|---|---|---|---|---|---|---|
| 00 | 371 | 80.8 | 56.6 | -24.2 | -75.7 | -7.0 |
| 01 | 378 | 75.7 | 50.4 | -25.3 | -74.4 | -8.9 |
| 02 | 380 | 69.5 | 44.6 | -24.9 | -68.2 | -10.4 |
| 03 | 381 | 63.9 | 39.9 | -24.0 | -64.6 | -10.5 |
| 04 | 378 | 58.9 | 35.8 | -23.0 | -60.9 | -10.5 |
| 05 | 377 | 55.5 | 34.0 | -21.5 | -58.6 | -9.2 |
| 06 | 380 | 53.7 | 32.2 | -21.4 | -55.8 | -10.0 |
| 07 | 385 | 53.4 | 34.2 | -19.2 | -48.5 | -9.4 |
| 08 | 388 | 58.4 | 36.0 | -22.4 | -51.1 | -12.4 |
| 09 | 385 | 64.7 | 34.3 | -30.4 | -63.9 | -19.0 |
| 10 | 367 | 64.2 | 31.1 | -33.1 | -72.6 | -21.2 |
| 11 | 363 | 66.4 | 28.8 | -37.6 | -81.4 | -24.3 |
| 12 | 359 | 65.1 | 28.6 | -36.6 | -84.0 | -22.5 |
| 13 | 364 | 62.5 | 28.3 | -34.2 | -82.2 | -19.9 |
| 14 | 368 | 56.3 | 28.1 | -28.2 | -69.0 | -16.3 |
| 15 | 387 | 54.3 | 28.4 | -25.9 | -64.3 | -13.1 |
| 16 | 383 | 50.4 | 29.7 | -20.8 | -51.9 | -10.1 |
| 17 | 382 | 50.0 | 34.8 | -15.2 | -41.1 | -6.6 |
| 18 | 385 | 55.4 | 44.4 | -11.0 | -41.0 | -0.9 |
| 19 | 389 | 66.3 | 53.8 | -12.5 | -55.3 | +1.9 |
| 20 | 382 | 76.5 | 59.9 | -16.5 | -67.5 | +0.6 |
| 21 | 383 | 83.9 | 63.2 | -20.7 | -70.7 | -3.7 |
| 22 | 383 | 85.6 | 63.9 | -21.7 | -70.9 | -5.5 |
| 23 | 384 | 83.8 | 61.8 | -22.0 | -73.8 | -4.9 |

## 5) Licence / attribution

- 8634 US Diplomatic Post: Islamabad (StateAir Islamabad): licenses field = null
- 233470 Islamabad (AirNow): licenses field = US Public Domain (attribution: Unknown Governmental Organization, None; from 2016-01-30)
- 4554236 Rawalpindi Women University (AirGradient): licenses field = CC BY 4.0 (attribution: The Urban Unit, None; from 2023-07-15)
- 4556719 Wasa 3, OHR Office (AirGradient): licenses field = CC BY 4.0 (attribution: The Urban Unit, None; from 2023-07-15)
- 4565419 Social Welfare Department (AirGradient): licenses field = CC BY 4.0 (attribution: The Urban Unit, None; from 2023-07-15)
- licence 33: US Public Domain — commercial True, attribution required False, share-alike False, modification True, redistribution True; http://www.usa.gov/publicdomain/label/1.0/
- licence 41: CC BY 4.0 — commercial True, attribution required True, share-alike False, modification True, redistribution True; https://creativecommons.org/licenses/by/4.0/

**https://docs.openaq.org/about/terms** (HTTP 200)

> …es and timezones Geospatial queries Client libraries Examples Examples Resources Countries Instruments Latest Licenses Locations Manufacturers Measurements Owners Parameters Providers Sensors Errors About 401 - Unauthorized 4…
> …instrument by ID Get instruments Get instruments by manufacturer ID Get a location by ID Get locations Get a license by ID Get licenses Get a parameter by ID Get a parameters Get a country by ID Get countries Get a manufactu…
> …software components of our tooling, including the API codebase, in accordance with the applicable open-source license. However, utilizing our official, hosted API implementation to develop products or services that substantia…
> …und to be in violation of this clause. This provision does not limit the rights granted under the open-source license for the software itself, but governs the use of our hosted API service. Intellectual Property and Attributi…
> …s provide their air quality data under terms that require source attribution—sometimes under Creative Commons licenses or open government licenses, and sometimes under bespoke terms. Regardless of such requirements, we believ…
> …ess OpenAQ Platform at rates higher than the documented rate limit must comply with the payment terms and API License and Services Agreement required by OpenAQ. Disclaimer Section titled “Disclaimer” IMPORTANT: Although OpenA…

**https://www.airnow.gov/airnow-data-exchange-guidelines/** (HTTP 404)

> (no matching text found / page not fetched)

**https://www.airgradient.com/open-data/** (HTTP 404)

> (no matching text found / page not fetched)

## Errors

- none
