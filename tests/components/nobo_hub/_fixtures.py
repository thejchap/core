"""Tryke fixtures for Nobø Ecohub tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.nobo_hub.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_unload_entry() -> Generator[AsyncMock]:
    """Override async_unload_entry."""
    with patch(
        "homeassistant.components.nobo_hub.async_unload_entry", return_value=True
    ) as mock_unload_entry:
        yield mock_unload_entry
