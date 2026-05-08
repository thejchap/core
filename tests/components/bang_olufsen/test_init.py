"""Test the bang_olufsen __init__."""

from unittest.mock import AsyncMock

from aiohttp.client_exceptions import ServerTimeoutError
from tryke import Depends, expect, fixture, test

from homeassistant.components.bang_olufsen import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceRegistry

from ._fixtures import mock_config_entry, mock_mozart_client
from .const import TEST_FRIENDLY_NAME, TEST_MODEL_BALANCE, TEST_SERIAL_NUMBER

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import mock_async_zeroconf


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zc: None = Depends(mock_async_zeroconf),
) -> None:
    """Per-module trigger to anchor fixture resolution."""


@test
async def setup_entry(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_mozart_client: AsyncMock = Depends(mock_mozart_client),
) -> None:
    """Test async_setup_entry."""
    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, TEST_SERIAL_NUMBER)}
    )
    expect(device).not_.to_be(None)
    expect(device.name).to_equal(TEST_FRIENDLY_NAME)
    expect(device.model).to_equal(TEST_MODEL_BALANCE)

    expect(mock_mozart_client.check_device_connection.call_count).to_equal(1)
    expect(mock_mozart_client.close_api_client.call_count).to_equal(0)
    expect(mock_mozart_client.connect_notifications.call_count).to_equal(1)


@test
async def setup_entry_failed(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_mozart_client: AsyncMock = Depends(mock_mozart_client),
) -> None:
    """Test failed async_setup_entry."""
    mock_mozart_client.check_device_connection.side_effect = ExceptionGroup(
        "", (ServerTimeoutError(), TimeoutError())
    )

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)

    expect(mock_mozart_client.check_device_connection.call_count).to_equal(1)
    expect(mock_mozart_client.close_api_client.call_count).to_equal(1)
    expect(mock_mozart_client.connect_notifications.call_count).to_equal(0)


@test
async def unload_entry(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_mozart_client: AsyncMock = Depends(mock_mozart_client),
) -> None:
    """Test unload_entry."""
    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(hasattr(mock_config_entry, "runtime_data")).to_be(True)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)

    expect(mock_mozart_client.disconnect_notifications.call_count).to_equal(1)
    expect(mock_mozart_client.close_api_client.call_count).to_equal(1)

    expect(hasattr(mock_config_entry, "runtime_data")).to_be(False)
    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
