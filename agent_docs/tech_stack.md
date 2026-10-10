# Tech stack

- Python 3.10+ (venv pinned to 3.12 via uv), Windows + Git Bash (`source .venv/Scripts/activate`)
- uv for env + installs; `requirements.txt` is the lock-ish record
- torch CPU-only (`--index-url https://download.pytorch.org/whl/cpu`)
- tinker (LoRA fine-tuning, remote) — key `TINKER_API_KEY` in `.env`
- tabpfn (tabular forecasting) — `TABPFN_TOKEN` in `.env`
- pandas, scikit-learn, requests, astral (sun times), pydantic, python-dotenv
- Data: iNaturalist API v1 (per-record CC licenses; <=1 req/s)
- Weather: Open-Meteo archive API — data CC BY 4.0, attribution required: "Weather data by Open-Meteo.com (CC BY 4.0)"
- Optional: Tiger Data, Sentry. No other sponsor tools.
