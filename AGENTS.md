# AGENTS.md — rules for any coding agent on field-window

1. Read `MEMORY.md` first, every task. Update it last (summarize, don't dump logs).
2. Small increments. Commit after each working increment (Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:`).
3. Edit only relevant files. Ask before big refactors or heavy new dependencies.
4. Secrets live only in `.env` (git-ignored). Never print, log or commit secrets.
5. Raw downloaded data goes in `data/raw/` (git-ignored). Keep `license` + `source_url` per record. Only redistribute records whose license allows it, with attribution.
6. NEVER invent records, observations, quotes, people or results. Unknown values stay `{{PLACEHOLDER}}`.
7. Held-out set is evaluated ONCE, at the end. All decisions use the dev split.
8. Synthetic data may only augment training. Never in dev, held-out, the forecaster, or any quote.
9. Status vocabulary in `MEMORY.md`: `planned` / `implemented` / `tested` / `verified`. Never upgrade a status without evidence (command + output).
10. Scope: Tinker + TabPFN core. Tiger Data and Sentry optional. No other sponsor tools.
11. Respect API rate limits. iNaturalist: <=1 request/second, descriptive User-Agent.
12. Never overwrite or re-run anything touching `results/forecast_2026-10-11.json` or `results/forecast_2026-10-11.md`. Those are the pre-registered, frozen files. Read-only.
13. Don't run final scoring until the user says so. Today isn't over; a full scoring run now would be premature and we'd have to redo it.
14. Don't make the repo public or touch GitHub repo settings. That's a manual step for tomorrow morning.
15. Don't force-push, and don't amend or rewrite existing commits.
16. Don't touch `.env` or print its contents.

Context: `agent_docs/project_brief.md`, `agent_docs/tech_stack.md`, `agent_docs/testing.md`. Before committing: `REVIEW-CHECKLIST.md`.
