"""iNaturalist data probe: counts + small sample only. Re-runnable.

Usage: .venv/Scripts/python scripts/data_probe.py
Writes results/data_probe.md (aggregates only) and data/raw/probe_sample_aves.json (git-ignored).
Rate limit: >=1.1 s between requests.
"""
from __future__ import annotations

import json
import statistics
import time
from collections import Counter
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.inaturalist.org/v1"
UA = "field-window/0.1 (DEV Hacktoberfest hackathon research probe; low-volume, 1 req/s)"
AREA = {"lat": 33.72, "lng": 73.06, "radius": 25}
OPEN_LICENSES = {"cc0", "cc-by", "cc-by-nc"}

session = requests.Session()
session.headers["User-Agent"] = UA
_last = 0.0


def get(path: str, **params) -> dict:
    global _last
    wait = 1.1 - (time.monotonic() - _last)
    if wait > 0:
        time.sleep(wait)
    for attempt in range(5):
        try:
            r = session.get(f"{API}/{path}", params=params, timeout=60)
        except requests.ConnectionError:
            _last = time.monotonic()
            if attempt == 4:
                raise
            time.sleep(5 * (attempt + 1))
            continue
        _last = time.monotonic()
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(10 * (attempt + 1))
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()
    return {}


def total(base: dict, **extra) -> int:
    return get("observations", **base, **extra, per_page=0)["total_results"]


def sample_stats(base: dict, n: int = 600) -> tuple[dict, list[dict]]:
    obs: list[dict] = []
    page = 1
    while len(obs) < n:
        res = get("observations", **base, per_page=200, page=page, order_by="id", order="desc")["results"]
        if not res:
            break
        obs += res
        page += 1
    obs = obs[:n]
    descs = [(o.get("description") or "").strip() for o in obs]
    nonempty = [d for d in descs if d]
    stats = {
        "n": len(obs),
        "pct_time_observed_at": 100 * sum(bool(o.get("time_observed_at")) for o in obs) / max(len(obs), 1),
        "pct_description": 100 * len(nonempty) / max(len(obs), 1),
        "licenses": Counter(o.get("license_code") or "null" for o in obs).most_common(),
        "median_desc_len": statistics.median(len(d) for d in nonempty) if nonempty else 0,
    }
    # Keep only non-personal fields for the raw sample.
    slim = [{
        "id": o["id"], "uri": o.get("uri"), "license_code": o.get("license_code"),
        "observed_on": o.get("observed_on"), "time_observed_at": o.get("time_observed_at"),
        "taxon": (o.get("taxon") or {}).get("name"), "description": o.get("description"),
    } for o in obs]
    return stats, slim


def main() -> None:
    md: list[str] = ["# iNaturalist data probe", "",
                     f"Area: lat {AREA['lat']}, lng {AREA['lng']}, radius {AREA['radius']} km; quality_grade=research. "
                     f"Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} by `scripts/data_probe.py`. "
                     "Aggregates only.", ""]
    base = {**AREA, "quality_grade": "research"}
    aves = {**base, "iconic_taxa": "Aves"}

    # a) totals
    t_all, t_aves = total(base), total(aves)
    md += ["## a) Totals", "", f"- All taxa: **{t_all}**", f"- Aves: **{t_aves}**", ""]

    # b) Aves breakdowns
    years = get("observations/histogram", **aves, interval="year", date_field="observed")["results"]["year"]
    sep_nov = total(aves, month="9,10,11")
    days = get("observations/histogram", **aves, interval="day", date_field="observed")["results"]["day"]
    distinct_days = sum(1 for v in days.values() if v > 0)
    sc_leaf = get("observations/species_counts", **aves, per_page=0)["total_results"]
    sc_species = get("observations/species_counts", **aves, hrank="species", lrank="species", per_page=0)["total_results"]
    top = get("observations/species_counts", **aves, per_page=25)["results"]
    md += ["## b) Aves", "", "Count by year (observed date):", "", "| Year | Count |", "|---|---|"]
    md += [f"| {y[:4]} | {c} |" for y, c in sorted(years.items()) if c]
    md += ["", f"- Sep–Nov (any year): **{sep_nov}**",
           f"- Distinct observation dates: **{distinct_days}**",
           f"- Distinct species (rank=species): **{sc_species}** (leaf taxa incl. subspecies/genus: {sc_leaf})", "",
           "Top 25 species:", "", "| # | Scientific name | Common name | Count |", "|---|---|---|---|"]
    md += [f"| {i} | {r['taxon']['name']} | {r['taxon'].get('preferred_common_name', '')} | {r['count']} |"
           for i, r in enumerate(top, 1)]
    md.append("")

    # c) sample stats
    stats, slim = sample_stats(aves)
    raw = ROOT / "data" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "probe_sample_aves.json").write_text(json.dumps(slim, ensure_ascii=False, indent=1), encoding="utf-8")
    md += [f"## c) Aves sample (n={stats['n']}, most recent by id)", "",
           f"- With time_observed_at: **{stats['pct_time_observed_at']:.1f}%**",
           f"- With non-empty description: **{stats['pct_description']:.1f}%**",
           f"- Median description length (non-empty): **{stats['median_desc_len']}** chars",
           "- License breakdown: " + ", ".join(f"{k}: {v}" for k, v in stats["licenses"]), ""]

    # d) example descriptions
    ex = [o for o in slim if o["license_code"] in OPEN_LICENSES and (o["description"] or "").strip()]
    md += ["## d) Example descriptions (cc0 / cc-by / cc-by-nc only, truncated to 120 chars)", ""]
    if not ex:
        md.append("_None found in sample._")
    for o in ex[:5]:
        text = " ".join(o["description"].split())[:120].replace("|", "/")
        md.append(f"- `{o['license_code']}` — \"{text}\" — {o['uri']}")
    md += ["", "Attribution: iNaturalist observers, per-record license; see each source URL.", ""]

    # e) Margalla Hills National Park
    md += ["## e) Margalla Hills National Park", ""]
    places = get("places/autocomplete", q="Margalla Hills National Park")["results"]
    place = next((p for p in places if "margalla" in p["display_name"].lower()), None)
    if not place:
        md.append("Could not resolve place_id.")
    else:
        pbase = {"place_id": place["id"], "quality_grade": "research"}
        paves = {**pbase, "iconic_taxa": "Aves"}
        pstats, _ = sample_stats(paves)
        md += [f"place_id **{place['id']}** ({place['display_name']})", "",
               f"- All taxa: **{total(pbase)}**", f"- Aves: **{total(paves)}**",
               f"- Aves sample n={pstats['n']}: time_observed_at {pstats['pct_time_observed_at']:.1f}%, "
               f"description {pstats['pct_description']:.1f}%, median desc len {pstats['median_desc_len']}",
               "- License breakdown: " + ", ".join(f"{k}: {v}" for k, v in pstats["licenses"]), ""]

    out = ROOT / "results" / "data_probe.md"
    out.write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    print(f"\nwrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
