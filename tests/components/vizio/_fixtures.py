"""Tryke fixtures for the Vizio integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture


@fixture
def vizio_get_unique_id() -> Generator[None]:
    """Mock get vizio unique ID."""
    from .const import UNIQUE_ID

    with patch(
        "homeassistant.components.vizio.config_flow.VizioAsync.get_unique_id",
        AsyncMock(return_value=UNIQUE_ID),
    ):
        yield


@fixture
def vizio_connect() -> Generator[None]:
    """Mock valid vizio device and entry setup."""
    with patch(
        "homeassistant.components.vizio.config_flow.VizioAsync.validate_ha_config",
        AsyncMock(return_value=True),
    ):
        yield


@fixture
def vizio_bypass_setup() -> Generator[None]:
    """Mock component setup."""
    with patch("homeassistant.components.vizio.async_setup_entry", return_value=True):
        yield
