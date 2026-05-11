"""Tryke fixtures for the Anthem AV integration."""

from collections.abc import Callable, Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture

from homeassistant.components.anthemav.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_MODEL, CONF_PORT
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


def get_zone() -> MagicMock:
    """Return a mocked zone."""
    zone = MagicMock()
    zone.power = False
    return zone


@fixture
def mock_anthemav() -> AsyncMock:
    """Return the default mocked anthemav."""
    avr = AsyncMock()
    avr.protocol.macaddress = "000000000001"
    avr.protocol.model = "MRX 520"
    avr.reconnect = AsyncMock()
    avr.protocol.wait_for_device_initialised = AsyncMock()
    avr.close = MagicMock()
    avr.protocol.input_list = []
    avr.protocol.audio_listening_mode_list = []
    avr.protocol.zones = {1: get_zone(), 2: get_zone()}
    return avr


@fixture
def mock_connection_create(
    mock_anthemav: AsyncMock = Depends(mock_anthemav),
) -> Generator[AsyncMock]:
    """Return the default mocked connection.create."""
    with patch(
        "anthemav.Connection.create",
        return_value=mock_anthemav,
    ) as mock:
        yield mock


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Anthem AV",
        data={
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 14999,
            CONF_MAC: "00:00:00:00:00:01",
            CONF_MODEL: "MRX 520",
        },
        unique_id="00:00:00:00:00:01",
    )


@fixture
def update_callback(
    mock_connection_create: AsyncMock = Depends(mock_connection_create),
) -> Callable[[str], None]:
    """Return the update_callback used when creating the connection."""
    return mock_connection_create.call_args[1]["update_callback"]


@fixture
async def init_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_connection_create: AsyncMock = Depends(mock_connection_create),
) -> MockConfigEntry:
    """Set up the AnthemAv integration for testing."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
