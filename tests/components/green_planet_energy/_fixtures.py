"""Tryke fixtures for the Green Planet Energy integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture

from homeassistant.components.green_planet_energy.const import DOMAIN

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={},
        unique_id=DOMAIN,
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock async_setup_entry."""
    with patch(
        "homeassistant.components.green_planet_energy.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_api() -> Generator[MagicMock]:
    """Mock Green Planet Energy API."""
    with (
        patch(
            "homeassistant.components.green_planet_energy.coordinator.GreenPlanetEnergyAPI",
            autospec=True,
        ) as mock_api_class,
        patch(
            "homeassistant.components.green_planet_energy.config_flow.GreenPlanetEnergyAPI",
            new=mock_api_class,
        ),
    ):
        mock_api_instance = MagicMock()
        today_prices = {
            f"gpe_price_{hour:02d}": 20.0 + (hour * 1.0) for hour in range(24)
        }
        tomorrow_prices = {
            f"gpe_price_{hour:02d}_tomorrow": 25.0 + (hour * 1.0) for hour in range(24)
        }
        all_prices = {**today_prices, **tomorrow_prices}
        mock_api_instance.get_electricity_prices = AsyncMock(return_value=all_prices)
        mock_api_instance.get_highest_price_today.return_value = 43.0
        mock_api_instance.get_highest_price_today_with_hour.return_value = (43.0, 23)
        mock_api_instance.get_lowest_price_day.return_value = 26.0
        mock_api_instance.get_lowest_price_day_with_hour.return_value = (26.0, 6)
        mock_api_instance.get_lowest_price_night.return_value = 20.0
        mock_api_instance.get_lowest_price_night_with_hour.return_value = (20.0, 0)

        def get_current_price_mock(data, hour):
            return 20.0 + (hour * 1.0)

        mock_api_instance.get_current_price.side_effect = get_current_price_mock
        mock_api_class.return_value = mock_api_instance
        yield mock_api_instance
