# Review checklist (before every commit)

- [ ] No secrets in diff (`git diff --cached | grep -iE "key|token|secret"` reviewed)
- [ ] No raw data in git (`git diff --cached --stat` shows nothing under `data/raw/`, no `labels/*.jsonl` except `labels/sample.jsonl`)
- [ ] No invented values; unknowns are `{{PLACEHOLDER}}`
- [ ] Any redistributed record has license + source URL + attribution
- [ ] Held-out set not touched (unless this is the final evaluation)
- [ ] Status changes in MEMORY.md backed by command + output
- [ ] MEMORY.md updated
