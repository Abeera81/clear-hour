# field-window

Hackathon project (DEV Hacktoberfest Week 1 "Touch Grass"). Work in progress.

Uses openly licensed public observation records (iNaturalist) near Islamabad/Rawalpindi and Open-Meteo weather to (a) fine-tune a small model on Tinker and (b) forecast likely observations on an outing with TabPFN.

## Setup (Windows + Git Bash)

```bash
uv venv --python 3.12
source .venv/Scripts/activate
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
uv pip install -r requirements.txt
cp .env.example .env   # fill in keys
python scripts/probes.py
```

## Attribution

- Observation data: iNaturalist contributors, per-record licenses (see each record's `license` + `source_url`).
- Weather data by [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0).

## License

Code: MIT (see LICENSE). Data keeps its original licenses.
