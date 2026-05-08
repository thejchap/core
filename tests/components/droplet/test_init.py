"""Test Droplet initialization."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import (
    mock_config_entry,
    mock_droplet,
    mock_droplet_connection,
    mock_droplet_discovery,
    mock_timeout,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import caplog as caplog_fixture, hass as hass_fixture, mock_network
from tests.hass_fixtures import LogCapture


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _timeout: None = Depends(mock_timeout),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def setup_no_version_info(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _discovery: AsyncMock = Depends(mock_droplet_discovery),
    _connection: AsyncMock = Depends(mock_droplet_connection),
    droplet: AsyncMock = Depends(mock_droplet),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test coordinator setup where Droplet never sends version info."""
    droplet.version_info_available.return_value = False
    await setup_integration(hass, config_entry)

    expect("Failed to get version info from Droplet" in caplog.text).to_be(True)


@test
async def setup_droplet_offline(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _discovery: AsyncMock = Depends(mock_droplet_discovery),
    _connection: AsyncMock = Depends(mock_droplet_connection),
    droplet: AsyncMock = Depends(mock_droplet),
) -> None:
    """Test integration setup when Droplet is offline."""
    droplet.connected = False
    await setup_integration(hass, config_entry)

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
