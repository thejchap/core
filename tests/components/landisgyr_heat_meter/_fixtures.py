"""Tryke fixtures for Landis + Gyr Heat Meter tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.landisgyr_heat_meter.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        yield mock_setup
