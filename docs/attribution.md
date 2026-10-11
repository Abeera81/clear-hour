# Attribution and licences

Everything below was read from the actual files or pages on 2026-10-11; verbatim quotes are in blockquotes.
Text marked **(ours)** is wording we chose, not wording supplied by the licensor.

## TabPFN v2 — Prior Labs

**Finding: the v2 weights are NOT plain Apache-2.0.** Two different licences are involved:

| Thing | Where we looked | What it says |
|---|---|---|
| `tabpfn` Python package 9.1.0 (code) | `.venv/Lib/site-packages/tabpfn-9.1.0.dist-info/licenses/LICENSE`, `METADATA` | Apache License 2.0 (`License-Expression: Apache-2.0`). `NOTICE`: "TabPFN / Copyright (c) 2026 Prior Labs GmbH". `THIRD-PARTY-NOTICES.md`: only skrub `SquashingScaler` (BSD-3-Clause). |
| v2 model weights we used (`tabpfn-v2-regressor.ckpt`) | The `.ckpt` files contain no licence text. The weights come from Hugging Face repos `Prior-Labs/TabPFN-v2-reg` (and `-clf`, used only in the capability probe), whose model card and `LICENSE.txt` we read | Card metadata: `license: other`, `license_name: priorlabs-1-1`, `license_link: https://github.com/PriorLabs/TabPFN/blob/49394b053a6759cfe68e90c21a2d51c31b396768/LICENSE`. Card text: "**License:** Prior Labs License (Apache 2.0 with additional attribution requirement)". Repo `LICENSE.txt` (identical in the `-reg` and `-clf` repos and byte-identical to the GitHub file at the linked commit; sha256 `08b1851b4b6136b5fb0cb124d3258e0d91e3e1623f1be5904b77e4d270d112d8`; repos not gated; model repo last modified 2025-11-04) = **Prior Labs License, Version 1.1, May 2025**. |

A copy of that licence is in [`docs/licenses/PriorLabs-TabPFN-v2-LICENSE.txt`](licenses/PriorLabs-TabPFN-v2-LICENSE.txt).
(The package's Apache-2.0 `LICENSE` file is for the code. The package's licence-acceptance gate, `browser_auth.py`, applies to v2.5 and newer, not to v2, which downloads without it.)

The licence's own summary: "This license is a derivative of the Apache 2.0 license (http://www.apache.org/licenses/) with a single modification: The added Paragraph 10 introduces an enhanced attribution requirement inspired by the Llama 3 license."

The added paragraph, verbatim:

> 10. Additional attribution.
> If You distribute or make available the Work or any Derivative
> Work thereof relating to any part of the source or model weights,
> or a product or service (including another AI model) that contains
> any source or model weights, You shall (A) provide a copy of this
> License with any such materials; and (B) prominently display
> “Built with PriorLabs-TabPFN” on each related website, user interface, blogpost,
> about page, or product documentation. If You use the source or model
> weights or model outputs to create, train, fine tune, distil, or
> otherwise improve an AI model, which is distributed or made available,
> you shall also include “TabPFN” at the beginning of any such AI model name.
> To clarify, internal benchmarking and testing without external
> communication shall not qualify as distribution or making available
> pursuant to this Section 10 and no attribution under this Section 10
> shall be required.

How we comply (our reading, not legal advice):
- **Exact wording used:** `Built with PriorLabs-TabPFN`.
- **Displayed on:** the top of `README.md`, the header and footer of the demo page (`docs/index.html`). It must also be included in any DEV post or blog write-up.
- **Licence copy included:** `docs/licenses/PriorLabs-TabPFN-v2-LICENSE.txt` (paragraph 10(A)). This repository does not contain or redistribute the weights; users download them from Hugging Face themselves.
- **Model naming:** we do not create, train, fine-tune or distil a separate AI model from TabPFN weights or outputs, and nothing named "Clear Hour" is a trained model artefact; the TabPFN regressor is used as-is and always labelled "TabPFN v2". If the project is ever described as an AI model derived from TabPFN, the "TabPFN" name-prefix rule in paragraph 10 would need to be revisited.
- **Citation (from the model card):** Hollmann, Müller, Purucker, Krishnakumar, Körfer, Hoo, Schirrmeister, Hutter (2025), "Accurate predictions on small data with a tabular foundation model", *Nature*, doi:10.1038/s41586-024-08328-6.
- **Earlier statements corrected:** our notes and earlier messages called the v2 weights "Apache-2.0 + attribution". That was an assumption; the accurate description is the Prior Labs License 1.1 above.

## Open-Meteo (weather and air quality)

- **Licence page** (https://open-meteo.com/en/licence), verbatim: "API data are offered under Attribution 4.0 International (CC BY 4.0)" … "Attribution: You must give appropriate credit, provide a link to the licence, and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use. You must include a link next to any location Open-Meteo data are displayed, for example: `<a href="https://open-meteo.com/">Weather data by Open-Meteo.com</a>`".
- **Air-quality docs** (https://open-meteo.com/en/docs/air-quality-api), "Citation & Acknowledgement", verbatim: "METEO FRANCE, Institut national de l'environnement industriel et des risques (Ineris), Aarhus University, Norwegian Meteorological Institute (MET Norway), Jülich Institut für Energie- und Klimaforschung (IEK), Institute of Environmental Protection – National Research Institute (IEP-NRI), Koninklijk Nederlands Meteorologisch Instituut (KNMI), Nederlandse Organisatie voor toegepast-natuurwetenschappelijk onderzoek (TNO), Swedish Meteorological and Hydrological Institute (SMHI), Finnish Meteorological Institute (FMI), Italian National Agency for New Technologies, Energy and Sustainable Economic Development (ENEA) and Barcelona Supercomputing Center (BSC) (2022): CAMS European air quality forecasts, ENSEMBLE data. Copernicus Atmosphere Monitoring Service (CAMS) Atmosphere Data Store (ADS). (Updated twice daily). **All users of Open-Meteo data must provide a clear attribution to CAMS ENSEMBLE data provider as well as a reference to Open-Meteo.**"
- **Caveat:** that citation names the *European* ENSEMBLE product. Our location (33.6 N, 73.05 E, Pakistan) is outside the European domain. The same page lists "CAMS Global Atmospheric Composition Forecasts … Global 0.4° (~45 km) … August 2022 onwards" as the global source, and the API returned grid point 33.6, 73.100006. The page gives no separate attribution wording for the global product, so we credit both below.
- **Terms** (https://open-meteo.com/en/terms): free API for non-commercial use, "Less than 10'000 API calls per day, 5'000 per hour and 600 per minute"; "You accept to the CC-BY 4.0 licence".
- **Attribution we use (ours):** "Weather data by [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0). Air-quality model data: Copernicus Atmosphere Monitoring Service (CAMS) via Open-Meteo (CAMS global atmospheric composition forecasts at this location; Open-Meteo credits the CAMS ENSEMBLE data providers listed above for its European product). Values were modified: bias-corrected and re-ranked by our models."

## OpenAQ and the sensor network

- **Ground truth:** OpenAQ location 4554236 "Rawalpindi Women University" (AirGradient, low-cost sensor). The OpenAQ API reports its licence as **CC BY 4.0** (licence id 41; commercial use, modification and redistribution allowed, attribution required) with attribution holder "**The Urban Unit**" (no URL supplied). The same holds for the second sensor used in the transfer test, 4565419 "Social Welfare Department".
- **Attribution we use (ours):** "Air-quality measurements: AirGradient sensors operated via The Urban Unit, CC BY 4.0, retrieved from [OpenAQ](https://openaq.org/). This does not imply endorsement by The Urban Unit; the sensor is uncalibrated and values were aggregated and modified."
- **OpenAQ terms** (https://docs.openaq.org/about/terms), verbatim excerpts: "OpenAQ users must therefore review and comply with any terms published by data providers."; "When required, OpenAQ users must acknowledge the original source(s) of any data they use, following the provider’s terms, and OpenAQ encourages users to acknowledge all original sources, even if the source does not require it."; free-API rate limit 60 requests/minute (`X-Ratelimit-Limit` header).
- **US Embassy Islamabad monitor** (OpenAQ 233470, AirNow feed): licence "US Public Domain" per OpenAQ. Used only for the validity check. The StateAir feed (8634) has `licenses: null` in OpenAQ; it appears only in aggregate CAMS-vs-monitor statistics in `results/ground_truth_probe.md`, never in a redistributed record.
- We do not redistribute raw sensor records in this repository: `data/raw/` and `data/processed/` are git-ignored. `results/*.json` contain model outputs and aggregates, plus (after scoring) the day's 24 hourly values for sensor 4554236, which carry the CC BY 4.0 attribution above.
