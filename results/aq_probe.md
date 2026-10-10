# Clear Hour — air-quality data feasibility probe

Location lat 33.6, lon 73.05 (Rawalpindi/Islamabad), timezone=auto. Run 2026-10-10 17:07 UTC by `scripts/aq_probe.py`. Aggregates only.

## 1) History depth

Earliest date with hourly pm2_5: **2022-08-04**

Search log (year steps, then binary search):

```
2025-01-01: data
2024-01-01: data
2023-01-01: data
2022-01-01: no data
2022-07-02: no data
2022-10-01: data
2022-08-16: data
2022-07-24: no data
2022-08-04: data
2022-07-29: no data
2022-08-01: no data
2022-08-02: no data
2022-08-03: no data
```

## 2) Coverage

Span 2022-08-04 00:00:00 → 2026-10-09 23:00:00 (Asia/Karachi, UTC offset 18000 s; grid point 33.6, 73.100006)

- Variables accepted: pm2_5, pm10, carbon_monoxide, nitrogen_dioxide, ozone, sulphur_dioxide
- Variables rejected: none
- Total hourly rows: **36672** (timestamps missing from the hourly grid: 0)

| Variable | % missing (null) |
|---|---|
| pm2_5 | 0.01% |
| pm10 | 0.01% |
| carbon_monoxide | 0.01% |
| nitrogen_dioxide | 0.01% |
| ozone | 0.01% |
| sulphur_dioxide | 0.01% |

| Year | Rows | pm2_5 non-null |
|---|---|---|
| 2022 | 3600 | 3595 |
| 2023 | 8760 | 8760 |
| 2024 | 8784 | 8784 |
| 2025 | 8760 | 8760 |
| 2026 | 6768 | 6768 |

Gaps in pm2_5 longer than 24 h: **0**

## 3) Seasonal / diurnal shape (pm2_5, µg/m³)

| Month | Mean pm2_5 | Hours |
|---|---|---|
| 1 | 58.1 | 2976 |
| 2 | 38.3 | 2712 |
| 3 | 29.6 | 2976 |
| 4 | 23.0 | 2880 |
| 5 | 28.2 | 2976 |
| 6 | 33.7 | 2880 |
| 7 | 41.2 | 2976 |
| 8 | 38.5 | 3643 |
| 9 | 40.3 | 3600 |
| 10 | 34.7 | 3192 |
| 11 | 43.9 | 2880 |
| 12 | 50.5 | 2976 |

| Hour (local) | Oct–Dec mean | Rest-of-year mean |
|---|---|---|
| 00 | 53.3 | 47.8 |
| 01 | 46.3 | 43.5 |
| 02 | 40.3 | 39.5 |
| 03 | 35.5 | 36.2 |
| 04 | 31.8 | 33.4 |
| 05 | 28.5 | 31.7 |
| 06 | 27.6 | 30.7 |
| 07 | 31.5 | 32.1 |
| 08 | 37.0 | 33.6 |
| 09 | 38.6 | 33.3 |
| 10 | 36.9 | 32.1 |
| 11 | 32.6 | 30.7 |
| 12 | 31.8 | 30.3 |
| 13 | 31.9 | 30.1 |
| 14 | 32.2 | 30.0 |
| 15 | 32.8 | 29.8 |
| 16 | 35.9 | 29.9 |
| 17 | 44.6 | 30.6 |
| 18 | 56.3 | 36.3 |
| 19 | 63.1 | 43.0 |
| 20 | 66.3 | 48.0 |
| 21 | 66.9 | 50.6 |
| 22 | 65.3 | 51.8 |
| 23 | 61.0 | 51.1 |

- Oct–Dec: min hour 06h (27.6), max hour 21h (66.9), max/min ratio **2.42**
- Rest of year: min hour 15h (29.8), max hour 22h (51.8), max/min ratio **1.73**

## 4) Forecast endpoint

- forecast_days=5: HTTP 200, 120 rows, non-null pm2_5 through **2026-10-14 23:00:00** (5 calendar days incl. today)
- forecast_days=7: HTTP 200, 168 rows, non-null pm2_5 through **2026-10-15 05:00:00** (6 calendar days incl. today)
- forecast_days=16: HTTP 400 — Forecast days is invalid. Allowed range 0 to 7. Given 7.
- past_days=3: HTTP 200, 72 past hours, 72 non-null (2026-10-07 00:00:00 → 2026-10-09 23:00:00)
- past_days vs history pull, 72 overlapping hours: mean |diff| 0.00, max 0.00

## 5) Weather join (Open-Meteo archive)

- Variables accepted: temperature_2m, wind_speed_10m, wind_direction_10m, pressure_msl, boundary_layer_height, relative_humidity_2m, precipitation
- Variables rejected: none
- Weather span 2022-08-04 00:00:00 → 2026-10-04 23:00:00, 36552 rows; timezone Asia/Karachi, UTC offset 18000 s (AQ: Asia/Karachi, 18000 s)
- AQ rows inside weather span: 36552; matched on identical timestamp: **36552** (100.00%)

| Weather variable | % missing in joined rows |
|---|---|
| temperature_2m | 0.00% |
| wind_speed_10m | 0.00% |
| wind_direction_10m | 0.00% |
| pressure_msl | 0.00% |
| boundary_layer_height | 11.95% |
| relative_humidity_2m | 0.00% |
| precipitation | 0.00% |

- boundary_layer_height null block: 2024-01-01 05:00:00 → 2024-07-01 04:00:00 (4368 h)

## 6) License / attribution (verbatim snippets from fetched pages)

**https://open-meteo.com/en/docs/air-quality-api** (HTTP 200)

> …application, or paste an API URL to restore its settings) Data Sources Forecast is based on the 11 kilometre CAMS European air quality forecast and the 45 kilometre CAMS global atmospheric composition forecasts. The Europea…
> …tes documentation . Data Set Region Spatial Resolution Temporal Resolution Data Availability Update frequency CAMS European Air Quality Forecast Europe 0.1° (~11 km) Hourly October 2023 onwards Every 24 hours, 4 days forecas…
> …ery 24 hours, 4 days forecast CAMS European Air Quality Reanalysis Europe 0.1° (~11 km) Hourly 2013 onwards - CAMS Global Atmospheric Composition Forecasts 🌍 Global 0.4° (~45 km) 3-Hourly August 2022 onwards Every 12 hours,…
> …recast 🌍 Global 0.1° (~11 km) 3-Hourly November 2024 onwards Every 24 hours, 5 days forecast Click to enlarge CAMS Europe Model Area. Source: Open-Meteo . API Documentation The API endpoint /v1/air-quality accepts a geograph…
> …onditions. domains String No auto Automatically combine both domains auto or specifically select the European cams_europe or global domain cams_global . timeformat String No iso8601 By default, timestamps use ISO 8601 format…
> …ve_pollen ragweed_pollen Instant Grains/m³ Pollen for various plants. Only available in Europe as provided by CAMS European Air Quality forecast. european_aqi european_aqi_pm2_5 european_aqi_pm10 european_aqi_nitrogen_dioxid…
> …ologies, Energy and Sustainable Economic Development (ENEA) and Barcelona Supercomputing Center (BSC) (2022): CAMS European air quality forecasts, ENSEMBLE data. Copernicus Atmosphere Monitoring Service (CAMS) Atmosphere Dat…
> …ere Data Store (ADS). (Updated twice daily). All users of Open-Meteo data must provide a clear attribution to CAMS ENSEMBLE data provider as well as a reference to Open-Meteo. Open-Meteo Features Pricing About us &amp; Conta…
> …e as current condition as well. Settings Global + European Domain ISO 8601 (e.g. 2026-10-09) Timeformat Usage licence: Non-Commercial Commercial Self-Hosted API Response Preview: Chart &amp; URL Python TypeScript Swift Other…
> …(CAMS) Atmosphere Data Store (ADS). (Updated twice daily). All users of Open-Meteo data must provide a clear attribution to CAMS ENSEMBLE data provider as well as a reference to Open-Meteo. Open-Meteo Features Pricing About us &am…

**https://open-meteo.com/en/licence** (HTTP 200)

> …) Icons from Weather Icons ( SIL OFL 1.1 ) Licence API data are offered under Attribution 4.0 International (CC BY 4.0) You are free to share: copy and redistribute the material in any medium or format and adapt: remix, transfor…
> …e from GeoNames ( CC-BY Licence ) Icons from Weather Icons ( SIL OFL 1.1 ) Licence API data are offered under Attribution 4.0 International (CC BY 4.0) You are free to share: copy and redistribute the material in any medium or form…
> …ext to any location Open-Meteo data are displayed, for example: &#x3C; a href = " https://open-meteo.com/ " > Weather data by Open-Meteo.com &#x3C;/ a > Open-Meteo is open-source Source code is available on GitHub under the GNU Affero…
> …om MeteoSwiss ( CC-BY Licence ) Wave forecasts from Copernicus Marine Service ( Licence ) Weather reanalysis, air quality forecasts and elevation data from Copernicus Climate Change Service C3S ( Licence ) Flood forecasts from Glob…
> …API DWD ICON API GEM API JMA API Met Norway API Other APIs Ensemble API Climate Change API Marine Weather API Air Quality API Geocoding API Elevation API Flood API External X Blog GitHub Mastodon Service status and uptime Model Upd…

**https://open-meteo.com/en/terms** (HTTP 200)

> …eo disclaims all liability under these Terms of Use, whether arising from contract, tort, or any other cause. Non-Commercial Use By using the Free API for non-commercial use you agree to following terms: Less than 10'000 API calls per…
> …than 10'000 API calls per day, 5'000 per hour and 600 per minute. You may only use the free API services for non-commercial purposes. You accept to the CC-BY 4.0 licence, as specified in the licence conditions . We reserve the right…
> …s . We reserve the right to block applications and IP addresses that misuse our service without prior notice. Non-commercial use is defined as elaborated by creative commons . To make it easier to understand, here are some examples th…
> …the purpose of sending you our newsletter and will not share or sell it with any third-party providers. Free Non-Commercial API Service We may collect non-personal information, such as IP addresses, for technical reasons such as serv…
> …arch at commercial entities. If you plan to use our service for commercial purposes or require additional API calls, we kindly request you to consider subscribing to our API plans as explained in detail on the pricing page. Y…
> …Free / Open-Access API Standard API Professional API Enterprise Commercial use ❌ ✅ ✅ ✅ Minutely Limit ⚠️ 600 calls / min ✅ Unlimited ✅ Unlimited ✅ Unlimited Hourly Limit ⚠️ 5.000 calls / hour ✅ Unlimited ✅ Unlimited ✅ Unlimi…
> …ed ✅ Unlimited Daily Limit ⚠️ 10.000 calls / day ✅ Unlimited ✅ Unlimited ✅ Unlimited Monthly Limit ⚠️ 300.000 calls / month ⚠️ 1M calls / month ⚠️ 5M calls / month ✅ >50M calls / month Privacy By using our service, you consen…
> …ividual log files will be removed, and only aggregated usage data will be retained, such as the number of API calls per day. We take appropriate measures to protect your personal information from unauthorized access, alterati…

## 7) Sanity — daily-mean pm2_5 extremes (days with ≥20 h)

| Rank | Highest day | Mean | Lowest day | Mean |
|---|---|---|---|---|
| 1 | 2024-11-14 | 110.6 | 2022-12-14 | 0.8 |
| 2 | 2024-11-10 | 99.5 | 2022-12-15 | 0.9 |
| 3 | 2024-12-23 | 97.4 | 2025-04-25 | 11.0 |
| 4 | 2024-01-20 | 93.7 | 2025-04-28 | 11.5 |
| 5 | 2024-01-16 | 93.2 | 2024-05-28 | 11.6 |

Suspected upstream artifacts (daily mean pm2_5 < 3 µg/m³, implausible for this city): **2022-12-14, 2022-12-15**

## Caveats

- Source is the CAMS **model** (global domain here: 0.4° ≈ 45 km grid, 3-hourly upstream, interpolated to hourly by Open-Meteo), not ground-station measurements. `past_days` returns the same model series as the history pull (see §4), so scoring a forecast against it scores against CAMS, not against measured air.
- Diurnal shape partly reflects CAMS model chemistry/BLH dynamics at 45 km, not a single street.

## Errors

- none
