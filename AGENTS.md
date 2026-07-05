# AGENTS.md

## Cursor Cloud specific instructions

### What this is
Single Python 3 CLI batch job (`pow_coin_monitor`): scans ~15 public web/API sources for newly-launched GPU/PoW mineable coins, scores/dedupes leads, and persists them to embedded SQLite plus JSON files under `data/`. It runs to completion and exits — there is **no long-running server, web UI, or API**.

### Environment
- System deps (`python3`, `python3-venv`, `python3-pip`, `git`, `curl`, `jq`) come from `.cursor/Dockerfile`. The startup update script refreshes the venv + pip deps into `.venv/`.
- Activate the interpreter as `.venv/bin/python3` (or `source .venv/bin/activate`).

### Run
- Core scan without any secrets (safe, recommended): `.venv/bin/python3 main.py --dry-run`
- Other flags: `--no-telegram` (scan + persist, skip alerts), `--json` (full JSON report), `--config <path>`.
- `./run.sh [flags]` also works but re-bootstraps the venv/env each time; prefer calling `main.py` directly once the venv exists.

### Non-obvious notes
- **Outbound internet is the only hard runtime dependency.** Every source is an external endpoint. Individual source failures are caught and logged per-source (see `pow_monitor/engine.py`); a run is still considered successful as long as some leads are produced. GitHub API 403 rate-limit and some 403/422 responses are expected without credentials and are non-fatal.
- **Telegram is optional.** Alerts only fire on a real (non-`--dry-run`) run when `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` are set in `.env` and there are new high-score leads. Nothing else needs these.
- **SQLite is embedded** (stdlib `sqlite3`, file at `data/coins.db`). No DB server to start. Note the table is named `leads` (not `coins`); scan metadata is in `scan_runs`.
- Outputs land in git-ignored `data/`: `coins.db`, `latest_scan.json`, `monitor.log`, and per-source `*_baseline.json` files. Baseline files suppress first-run flooding, so a fresh checkout's first run reports many "new" leads.
- No test suite and no linter are configured. Use `.venv/bin/python3 -m py_compile main.py pow_monitor/*.py pow_monitor/**/*.py` as a quick sanity check.
- `scripts/bootstrap_env.sh` / `.cursor/scripts/setup-ai-dev.sh` reference host-specific sibling paths (`~/Downloads/...`) that don't exist in the cloud VM; they no-op safely and are not required.
