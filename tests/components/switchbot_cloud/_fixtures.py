"""Tryke fixtures for SwitchBot Cloud tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.switchbot_cloud.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock
