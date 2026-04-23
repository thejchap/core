"""Tryke fixtures for Freedompro."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from .const import DEVICES, DEVICES_STATE


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.freedompro.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_freedompro() -> Generator[None]:
    """Mock freedompro get_list and get_states."""
    with (
        patch(
            "homeassistant.components.freedompro.coordinator.get_list",
            return_value={
                "state": True,
                "devices": DEVICES,
            },
        ),
        patch(
            "homeassistant.components.freedompro.coordinator.get_states",
            return_value=DEVICES_STATE,
        ),
    ):
        yield
