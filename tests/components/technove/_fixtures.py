"""Tryke fixtures for the TechnoVE integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from technove import Station as TechnoVEStation
from tryke import Depends, fixture

from homeassistant.components.technove.const import DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, load_json_object_fixture
from tests.hass_fixtures import hass as hass_fx


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.123"},
        unique_id="AA:AA:AA:AA:AA:BB",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.technove.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_onboarding() -> Generator[MagicMock]:
    """Mock that Home Assistant is currently onboarding."""
    with patch(
        "homeassistant.components.onboarding.async_is_onboarded",
        return_value=False,
    ) as mock_onboarding:
        yield mock_onboarding


@fixture
def device_fixture() -> TechnoVEStation:
    """Return the device fixture for a specific device."""
    return TechnoVEStation(load_json_object_fixture("station_charging.json", DOMAIN))


@fixture
def mock_technove(
    device_fixture: TechnoVEStation = Depends(device_fixture),
) -> Generator[MagicMock]:
    """Return a mocked TechnoVE client."""
    with (
        patch(
            "homeassistant.components.technove.coordinator.TechnoVE", autospec=True
        ) as technove_mock,
        patch(
            "homeassistant.components.technove.config_flow.TechnoVE", new=technove_mock
        ),
    ):
        technove = technove_mock.return_value
        technove.update.return_value = device_fixture
        technove.ip_address = "127.0.0.1"
        yield technove


@fixture
async def init_integration(
    hass: HomeAssistant = Depends(hass_fx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _technove: MagicMock = Depends(mock_technove),
) -> MockConfigEntry:
    """Set up the TechnoVE integration for testing."""
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    return config_entry
