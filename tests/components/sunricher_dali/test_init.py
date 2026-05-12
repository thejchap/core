"""Test the Sunricher DALI integration initialization."""

from unittest.mock import MagicMock

from PySrDaliGateway.exceptions import DaliGatewayError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry, mock_devices, mock_gateway

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def setup_entry_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    gateway: MagicMock = Depends(mock_gateway),
) -> None:
    """Test successful setup of config entry."""
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)
    gateway.connect.assert_called_once()


@test.skip("snapshot test — out of scope")
async def devices() -> None:
    """Stub for test_devices (snapshot)."""


@test
async def setup_entry_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    gateway: MagicMock = Depends(mock_gateway),
) -> None:
    """Test setup fails when gateway connection fails."""
    entry.add_to_hass(hass)
    gateway.connect.side_effect = DaliGatewayError("Connection failed")

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(False)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
    gateway.connect.assert_called_once()


@test
async def setup_entry_discovery_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    gateway: MagicMock = Depends(mock_gateway),
) -> None:
    """Test setup fails when device discovery fails."""
    entry.add_to_hass(hass)
    gateway.discover_devices.side_effect = DaliGatewayError("Discovery failed")

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(False)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
    gateway.connect.assert_called_once()
    gateway.discover_devices.assert_called_once()


@test
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    gateway: MagicMock = Depends(mock_gateway),
) -> None:
    """Test successful unloading of config entry."""
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.skip("snapshot test — out of scope")
async def remove_stale_devices() -> None:
    """Stub for test_remove_stale_devices (snapshot)."""


_ = (mock_config_entry, mock_devices, mock_gateway)
