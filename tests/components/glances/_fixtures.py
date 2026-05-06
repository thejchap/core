"""Tryke fixtures for the glances integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture

from . import HA_SENSOR_DATA


@fixture
def mock_api() -> Generator[MagicMock]:
    """Mock glances api."""
    with patch("homeassistant.components.glances.Glances") as mock_api:
        mock_api.return_value.get_ha_sensor_data = AsyncMock(
            return_value=HA_SENSOR_DATA
        )
        yield mock_api


@fixture
def glances_setup() -> Generator[None]:
    """Mock Glances entry setup."""
    with patch("homeassistant.components.glances.async_setup_entry", return_value=True):
        yield
