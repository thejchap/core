"""Tryke fixtures for kraken tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture


@fixture
def mock_call_rate_limit_sleep() -> Generator[None]:
    """Patch the call rate limit sleep time."""
    with patch(
        "homeassistant.components.kraken.coordinator.CALL_RATE_LIMIT_SLEEP", new=0
    ):
        yield
