"""Root conftest.py for swe_af test suite.

Shared fixtures:
- agentfield_server_guard: session-scoped autouse fixture that aborts the
  session if AGENTFIELD_SERVER points to a real external host.
- mock_agent_ai: function-scoped fixture that patches swe_af.app.app.call
  with an AsyncMock, isolating tests from real API calls.
- attach_fast_router: function-scoped fixture that wires fast_router to a
  mock agent to prevent RuntimeError on unattached router access.

_ENVELOPE_KEYS behavior:
  When mock_agent_ai.side_effect returns a dict containing any of the keys
  {"status", "result", "execution_id"}, the caller unwraps "result" as the
  payload. If the returned dict contains none of those keys it is treated as
  a fast-path plain dict (the payload itself). Tests can supply either form.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlparse

import pytest


# ---------------------------------------------------------------------------
# _is_real_host helper (exported so integration tests can verify its logic)
# ---------------------------------------------------------------------------


def _is_real_host(url: str) -> bool:
    """Return True if the URL points to a real (non-local) host."""
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    return hostname not in ("localhost", "127.0.0.1", "::1", "")


# ---------------------------------------------------------------------------
# agentfield_server_guard — session-scoped autouse
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def agentfield_server_guard() -> None:
    """Abort the test session if AGENTFIELD_SERVER points to a real host.

    All tests must run against a localhost URL. CI sets:
        AGENTFIELD_SERVER=http://localhost:9999
    Without this guard a misconfigured environment could make real API calls.
    """
    server = os.environ.get("AGENTFIELD_SERVER", "")
    if not server:
        pytest.skip(
            "AGENTFIELD_SERVER is not set — set it to a localhost URL to run tests"
        )
    if _is_real_host(server):
        pytest.exit(
            f"AGENTFIELD_SERVER={server!r} points to a real host. "
            "Tests must use a localhost URL (e.g. http://localhost:9999).",
            returncode=1,
        )


# ---------------------------------------------------------------------------
# mock_agent_ai — function-scoped patch of swe_af.app.app.call
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_agent_ai():
    """Patch swe_af.app.app.call with a fresh AsyncMock for each test.

    Usage:
        mock_agent_ai.side_effect = [result1, result2, ...]

    Each element of side_effect is the value returned by one call to
    app.call(). Tests supply plain dicts (fast-path) or envelope dicts.
    """
    with patch("swe_af.app.app.call", new_callable=AsyncMock) as mock_call:
        yield mock_call


# ---------------------------------------------------------------------------
# attach_fast_router — function-scoped fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def attach_fast_router():
    """Attach fast_router to a mock agent so router methods don't raise.

    Required by tests that call fast_router methods directly without going
    through the full app startup.
    """
    try:
        from swe_af.fast import fast_router

        mock_agent = MagicMock()
        object.__setattr__(fast_router, "_agent", mock_agent)
        yield mock_agent
    except ImportError:
        yield MagicMock()


# ---------------------------------------------------------------------------
# Demo-build Snowflake credential fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def env_with_creds(monkeypatch):
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "test_account")
    monkeypatch.setenv("SNOWFLAKE_USER", "test_user")
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "test_password")


@pytest.fixture
def env_missing_account(monkeypatch):
    monkeypatch.delenv("SNOWFLAKE_ACCOUNT", raising=False)
    monkeypatch.delenv("SNOWFLAKE_USER", raising=False)
    monkeypatch.delenv("SNOWFLAKE_PASSWORD", raising=False)
