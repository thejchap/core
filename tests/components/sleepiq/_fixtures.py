"""Tryke fixtures for SleepIQ tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

SLEEPIQ_CONFIG = {
    CONF_USERNAME: "user@email.com",
    CONF_PASSWORD: "password",
}


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.sleepiq.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry
