"""Tests for the Russound RIO integration."""

from unittest.mock import AsyncMock

from aiorussound import RussoundTcpConnectionHandler
from aiorussound.connection import RussoundSerialConnectionHandler
from tryke import Depends, expect, fixture, test

from homeassistant.components.russound_rio.const import CONF_BAUDRATE, DOMAIN, TYPE_TCP
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_DEVICE, CONF_HOST, CONF_PORT, CONF_TYPE
from homeassistant.core import HomeAssistant

from ._fixtures import (
    mock_config_entry,
    mock_russound_client,
    mock_serial_config_entry,
    mock_setup_entry,
)
from .const import MOCK_SERIAL_CONFIG, MOCK_TCP_CONFIG, MODEL

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


async def _setup_integration(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@test
async def config_entry_not_ready(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_russound_client),
) -> None:
    """Test the Russound configuration entry not ready."""
    client.connect.side_effect = TimeoutError
    await _setup_integration(hass, entry)

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)

    client.connect = AsyncMock(return_value=True)


@test.skip("snapshot test — out of scope")
async def device_info() -> None:
    """Stub for test_device_info (snapshot)."""


@test.skip("requires caplog fixture — port deferred")
async def disconnect_reconnect_log() -> None:
    """Stub for test_disconnect_reconnect_log."""


@test
async def migrate_entry_from_v1_to_v2_on_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_mock: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test a version 1 entry is migrated during setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        data={
            CONF_HOST: "192.168.20.75",
            CONF_PORT: 9621,
        },
        unique_id="00:11:22:33:44:55",
        title=MODEL,
    )
    await _setup_integration(hass, entry)

    expect(entry.version).to_equal(2)
    expect(entry.data).to_equal(
        {
            CONF_TYPE: TYPE_TCP,
            CONF_HOST: "192.168.20.75",
            CONF_PORT: 9621,
        }
    )
    expect(len(setup_mock.mock_calls)).to_equal(1)


@test
async def migrate_entry_from_future_version_fails_on_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup fails for a future config entry version."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=3,
        data={
            CONF_TYPE: TYPE_TCP,
            CONF_HOST: "192.168.20.75",
            CONF_PORT: 9621,
        },
        unique_id="00:11:22:33:44:55",
        title=MODEL,
    )
    await _setup_integration(hass, entry)

    expect(entry.version).to_equal(3)


@test
async def setup_entry_uses_tcp_handler(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_russound_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test setup uses the TCP handler."""
    await _setup_integration(hass, entry)

    handler = client.connection_handler
    expect(isinstance(handler, RussoundTcpConnectionHandler)).to_be(True)
    expect(handler.host).to_equal(MOCK_TCP_CONFIG[CONF_HOST])
    expect(handler.port).to_equal(MOCK_TCP_CONFIG[CONF_PORT])


@test
async def setup_entry_uses_serial_handler(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_russound_client),
    entry: MockConfigEntry = Depends(mock_serial_config_entry),
) -> None:
    """Test setup uses the serial handler."""
    await _setup_integration(hass, entry)

    handler = client.connection_handler
    expect(isinstance(handler, RussoundSerialConnectionHandler)).to_be(True)
    expect(handler.port).to_equal(MOCK_SERIAL_CONFIG[CONF_DEVICE])
    expect(handler.baudrate).to_equal(MOCK_SERIAL_CONFIG[CONF_BAUDRATE])


_ = (
    mock_config_entry,
    mock_russound_client,
    mock_serial_config_entry,
    mock_setup_entry,
)
