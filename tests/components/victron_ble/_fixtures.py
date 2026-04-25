"""Tryke fixtures for the Victron BLE integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from home_assistant_bluetooth import BluetoothServiceInfo
from tryke import Depends, fixture

from homeassistant.components.victron_ble.const import DOMAIN
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_ADDRESS
from homeassistant.core import HomeAssistant

from .fixtures import VICTRON_VEBUS_SERVICE_INFO, VICTRON_VEBUS_TOKEN

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.victron_ble.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_discovered_service_info() -> Generator[AsyncMock]:
    """Mock discovered service info."""
    with patch(
        "homeassistant.components.victron_ble.config_flow.async_discovered_service_info",
        return_value=[VICTRON_VEBUS_SERVICE_INFO],
    ) as mock_discovered_service_info:
        yield mock_discovered_service_info


@fixture
def service_info() -> BluetoothServiceInfo:
    """Return service info."""
    return VICTRON_VEBUS_SERVICE_INFO


@fixture
def access_token() -> str:
    """Return access token."""
    return VICTRON_VEBUS_TOKEN


@fixture
def mock_config_entry(
    service_info: BluetoothServiceInfo = Depends(service_info),
    access_token: str = Depends(access_token),
) -> MockConfigEntry:
    """Mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ADDRESS: service_info.address,
            CONF_ACCESS_TOKEN: access_token,
        },
        unique_id=service_info.address,
    )


@fixture
def mock_config_entry_added_to_hass(
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    hass: HomeAssistant = Depends(hass_fx),
) -> MockConfigEntry:
    """Mock config entry factory that added to hass."""
    entry = mock_config_entry
    entry.add_to_hass(hass)
    return entry
