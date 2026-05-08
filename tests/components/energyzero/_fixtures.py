"""Tryke fixtures for the EnergyZero integration."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

from energyzero import Electricity, Gas
from tryke import Depends, fixture

from homeassistant.components.energyzero.const import DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, async_load_json_object_fixture
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.energyzero.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="energy",
        domain=DOMAIN,
        data={},
        unique_id=DOMAIN,
        entry_id="12345",
    )


@fixture
async def mock_energyzero(
    hass: HomeAssistant = Depends(hass_fixture),
) -> AsyncGenerator[MagicMock]:
    """Return a mocked EnergyZero client."""
    with patch(
        "homeassistant.components.energyzero.coordinator.EnergyZero", autospec=True
    ) as energyzero_mock:
        client = energyzero_mock.return_value
        client.get_electricity_prices_legacy.return_value = Electricity.from_dict(
            await async_load_json_object_fixture(hass, "today_energy.json", DOMAIN)
        )
        client.get_gas_prices_legacy.return_value = Gas.from_dict(
            await async_load_json_object_fixture(hass, "today_gas.json", DOMAIN)
        )
        yield client
