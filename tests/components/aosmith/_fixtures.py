"""Tryke fixtures for the A. O. Smith integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from py_aosmith import AOSmithAPIClient
from tryke import Depends, fixture

from homeassistant.components.aosmith.const import DOMAIN
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM

from .conftest import ENERGY_USE_FIXTURE, build_device_fixture

from tests.common import MockConfigEntry, async_load_json_object_fixture
from tests.hass_fixtures import hass as hass_fx

FIXTURE_USER_INPUT = {
    CONF_EMAIL: "testemail@example.com",
    CONF_PASSWORD: "test-password",
}


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data=FIXTURE_USER_INPUT,
        unique_id=FIXTURE_USER_INPUT[CONF_EMAIL],
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.aosmith.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
async def mock_client(
    hass: HomeAssistant = Depends(hass_fx),
) -> MagicMock:
    """Return a mocked client."""
    get_devices_fixture = [
        build_device_fixture(
            heat_pump=True,
            mode_pending=False,
            setpoint_pending=False,
            has_vacation_mode=True,
            supports_hot_water_plus=False,
        )
    ]
    get_all_device_info_fixture = await async_load_json_object_fixture(
        hass, "get_all_device_info.json", DOMAIN
    )

    client_mock = MagicMock(AOSmithAPIClient)
    client_mock.get_devices = AsyncMock(return_value=get_devices_fixture)
    client_mock.get_energy_use_data = AsyncMock(return_value=ENERGY_USE_FIXTURE)
    client_mock.get_all_device_info = AsyncMock(
        return_value=get_all_device_info_fixture
    )

    return client_mock


@fixture
async def init_integration(
    hass: HomeAssistant = Depends(hass_fx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    client: MagicMock = Depends(mock_client),
) -> Generator[MockConfigEntry]:
    """Set up the integration for testing."""
    hass.config.units = US_CUSTOMARY_SYSTEM

    with patch(
        "homeassistant.components.aosmith.AOSmithAPIClient", return_value=client
    ):
        config_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        yield config_entry
