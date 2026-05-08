"""Tests for the NRGkick integration initialization."""

from unittest.mock import AsyncMock

from nrgkick_api import (
    NRGkickAPIDisabledError,
    NRGkickAuthenticationError,
    NRGkickConnectionError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.nrgkick.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from . import setup_integration
from ._fixtures import mock_config_entry, mock_nrgkick_api

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Force tryke fixture resolution before each test."""


@test
async def load_unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_nrgkick_api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test successful load and unload of entry."""
    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case(
        "auth_error",
        exception=NRGkickAuthenticationError,
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "api_disabled",
        exception=NRGkickAPIDisabledError,
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "connection_error",
        exception=NRGkickConnectionError,
        state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "timeout",
        exception=TimeoutError,
        state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "os_error",
        exception=OSError,
        state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def entry_setup_errors(
    *,
    exception: type[Exception],
    state: ConfigEntryState,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_nrgkick_api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test setup entry with failed connection."""
    mock_nrgkick_api.get_info.side_effect = exception

    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(state)


@test.skip("requires syrupy snapshot fixture (not in tryke shim)")
async def device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_nrgkick_api: AsyncMock = Depends(mock_nrgkick_api),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test successful load and unload of entry."""
