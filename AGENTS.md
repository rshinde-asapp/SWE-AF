# AGENTS.md

## Commands

```bash
# Install (editable + dev deps)
pip install -e ".[dev]"

# Test (stop on first failure, quiet)
make test
# or directly:
python -m pytest tests/ -x -q

# Test + compile check (what CI runs)
make check

# Single test file
python -m pytest tests/test_planner_pipeline.py -x -q

# Single test in fast/ subdirectory
python -m pytest tests/fast/test_planner.py -x -q

# Lint (ruff only — no formatter enforced)
python -m ruff check swe_af/
```

## Critical test requirement

**`AGENTFIELD_SERVER` must be set to a localhost URL** or tests abort immediately. CI uses `http://localhost:9999`. Without it:

```bash
AGENTFIELD_SERVER=http://localhost:9999 python -m pytest tests/ -x -q
```

The session-scoped `agentfield_server_guard` fixture in `tests/conftest.py` enforces this — it rejects any real external host.

## Package layout

```
swe_af/
  app.py              # Main agent: swe-planner (NODE_ID), port 8003
  fast/app.py         # Fast agent: swe-fast (NODE_ID), port 8004
  execution/          # DAG executor, coding loop, schemas, replanner
  reasoners/          # Planning pipeline agents (PM, architect, tech lead, etc.)
  prompts/            # Prompt templates per agent role
tests/
  conftest.py         # Root fixtures: agentfield_server_guard, mock_agent_ai, attach_fast_router
  fast/conftest.py    # Fast-pipeline fixtures
```

## Two entry points / two agents

- `swe-af` / `python -m swe_af` → full pipeline (plan → execute → verify → PR), port 8003
- `swe-fast` / `python -m swe_af.fast` → single-pass, sequential, port 8004

Both require an AgentField control-plane (`AGENTFIELD_SERVER`).

## SDK pin — do not bump without testing

`claude-agent-sdk==0.1.20` is pinned exactly. Newer builds produce `"Unknown message type: rate_limit_event"` during streaming. See comment in `pyproject.toml:11`.

## Runtime model config (V2 API)

Models are configured per-request in the `config` payload — **not** via env vars:

```json
{
  "runtime": "claude_code",
  "models": { "default": "sonnet", "coder": "opus" }
}
```

`runtime` values: `claude_code` | `open_code`. Legacy `ai_provider`, `preset`, `model` keys are removed.

## Mock fixture shape (important for tests)

`mock_agent_ai` patches `swe_af.app.app.call`. Return values must be either:
- **Fast-path**: plain dict with no envelope keys → `{"plan": [], "status": "planned"}`
- **Envelope**: `{"status": "success", "result": {...}, "execution_id": "x"}`

See `tests/conftest.py` docstring for `_ENVELOPE_KEYS` behavior.

## Docker / multi-service

```bash
# Full stack (control-plane + swe-agent + swe-fast)
docker compose up

# Local dev without Docker (control-plane already running elsewhere)
AGENTFIELD_SERVER=http://localhost:8080 python -m swe_af
```

`docker-compose.local.yml` exists for local overrides.

## Required env vars

| Var | Required | Notes |
|-----|----------|-------|
| `ANTHROPIC_API_KEY` | One of these | Claude backend |
| `CLAUDE_CODE_OAUTH_TOKEN` | One of these | Uses Pro/Max subscription |
| `OPENROUTER_API_KEY` | One of these | 200+ open models |
| `OPENAI_API_KEY` | One of these | GPT models |
| `AGENTFIELD_SERVER` | Yes at runtime | Default `http://localhost:8080` |
| `GH_TOKEN` | Optional | Draft PR creation only |

Copy `.env.example` → `.env` before running.

## CI

Runs `make check` (= `pytest` + `python -m compileall`) with `AGENTFIELD_SERVER=http://localhost:9999`. Python 3.12 only.

## Linter

`ruff` only. No black/isort enforced. `asyncio_mode = "auto"` in pytest config — no `@pytest.mark.asyncio` needed.
