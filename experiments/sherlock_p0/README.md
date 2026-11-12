# Sherlock P0 — isolated validation

Scope: experimental adapter only; no production route, scheduled job, or deployment changed.

## Setup

Use a Python virtual environment and install the official `sherlock-project` package.
```bash
python -m pip install sherlock-project
python -m unittest discover -s experiments/sherlock_p0 -p 'test_*.py' -v
python -m experiments.sherlock_p0.adapter davylab --site GitHub
```

Only search public organization or self-owned usernames for validation. Do not infer that identical usernames belong to the same person.

## Acceptance criteria

1. Unit tests pass (validation, safe argument construction, parsing, deduplication, mock execution and timeout).
2. Official Sherlock CLI installs and returns its version.
3. Controlled live lookup on a self-owned or organization account works; record command, duration, exit code and candidates.
4. Independently verify each candidate URL before labeling it confirmed; record false positives and network failures.
5. No production API changes; no API secrets in logs or artifacts.

## P1–P3 roadmap

- P1: authenticated opt-in POST /accounts/discover with rate limits, bounded concurrency, cache, job IDs and audit log; run as background worker rather than synchronous HTTP.
- P2: integrate candidate accounts into Event Radar, Topic Studio and AI Radar using provenance, explicit human verification and source-specific permissions.
- P3: scoring, freshness tracking, organization profile linking and explainable confidence. No automatic cross-person identity merging.

Do not expose unrestricted public username enumeration. Respect platform terms, privacy and request budgets.
