"""Fixtures for anthemav integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture

from homeassistant.components.anthemav.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_MODEL, CONF_PORT

from tests.common import MockConfigEntry


def _get_zone() -> MagicMock:
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
    avr.protocol.zones = {1: _get_zone(), 2: _get_zone()}
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
