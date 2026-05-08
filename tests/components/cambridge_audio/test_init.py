"""Tests for the Cambridge Audio integration."""

from unittest.mock import AsyncMock, Mock

from aiostreammagic import StreamMagicError
from aiostreammagic.models import CallbackType
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import mock_state_update, setup_integration
from ._fixtures import (
    mock_config_entry as mock_config_entry_fixture,
    mock_stream_magic_client,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def config_entry_not_ready(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_stream_magic_client: AsyncMock = Depends(mock_stream_magic_client),
) -> None:
    """Test the Cambridge Audio configuration entry not ready."""
    mock_stream_magic_client.connect = AsyncMock(side_effect=StreamMagicError())
    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)

    mock_stream_magic_client.connect = AsyncMock(return_value=True)


@test
async def disconnect_reconnect_log(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_stream_magic_client: AsyncMock = Depends(mock_stream_magic_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test device registry integration."""
    await setup_integration(hass, mock_config_entry)

    mock_stream_magic_client.is_connected = Mock(return_value=False)
    await mock_state_update(mock_stream_magic_client, CallbackType.CONNECTION)
    expect("Disconnected from device at 192.168.20.218" in caplog.text).to_be(True)

    mock_stream_magic_client.is_connected = Mock(return_value=True)
    await mock_state_update(mock_stream_magic_client, CallbackType.CONNECTION)
    expect("Reconnected to device at 192.168.20.218" in caplog.text).to_be(True)


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def device_info() -> None:
    """Stub for test_device_info."""
