"""Tryke fixtures for victron_gx tests."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture
from victron_mqtt import Hub as VictronVenusHub
from victron_mqtt.testing import create_mocked_hub

from homeassistant.components.victron_gx.const import (
    CONF_INSTALLATION_ID,
    CONF_MODEL,
    CONF_SERIAL,
    DOMAIN,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant

from .const import MOCK_HOST, MOCK_INSTALLATION_ID, MOCK_MODEL, MOCK_SERIAL

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx


@fixture
def mock_victron_hub_library() -> Generator[MagicMock]:
    """Mock the victron_mqtt library."""
    with patch("homeassistant.components.victron_gx.hub.VictronVenusHub") as mock_lib:
        hub_instance = MagicMock()
        hub_instance.connect = AsyncMock()
        hub_instance.disconnect = AsyncMock()
        hub_instance.installation_id = MOCK_INSTALLATION_ID
        mock_lib.return_value = hub_instance
        yield mock_lib


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCK_INSTALLATION_ID,
        data={
            CONF_HOST: MOCK_HOST,
            CONF_PORT: 1883,
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_pass",
            CONF_SSL: False,
            CONF_INSTALLATION_ID: MOCK_INSTALLATION_ID,
            CONF_MODEL: MOCK_MODEL,
            CONF_SERIAL: MOCK_SERIAL,
        },
        title=f"Victron OS {MOCK_INSTALLATION_ID} ({MOCK_HOST}:1883)",
    )


@fixture
async def init_integration(
    hass: HomeAssistant = Depends(hass_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> AsyncGenerator[tuple[VictronVenusHub, MockConfigEntry]]:
    """Set up the Victron GX MQTT integration for testing."""
    mock_config_entry.add_to_hass(hass)

    victron_hub = await create_mocked_hub()

    with patch(
        "homeassistant.components.victron_gx.hub.VictronVenusHub"
    ) as mock_hub_class:
        mock_hub_class.return_value = victron_hub

        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    yield victron_hub, mock_config_entry
