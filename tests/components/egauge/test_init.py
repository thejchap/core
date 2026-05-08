"""Tests for the eGauge integration."""

from unittest.mock import MagicMock

from egauge_async.exceptions import (
    EgaugeAuthenticationError,
    EgaugeParsingException,
    EgaugePermissionError,
)
from httpx import ConnectError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry, mock_egauge_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def setup_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: MagicMock = Depends(mock_egauge_client),
) -> None:
    """Test successful setup."""
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(client.get_device_serial_number.called).to_be(True)
    expect(client.get_hostname.called).to_be(True)
    expect(client.get_register_info.called).to_be(True)


@test.cases(
    test.case("connect", exception=ConnectError, expected=ConfigEntryState.SETUP_RETRY),
    test.case("auth", exception=EgaugeAuthenticationError, expected=ConfigEntryState.SETUP_ERROR),
    test.case("perm", exception=EgaugePermissionError, expected=ConfigEntryState.SETUP_ERROR),
    test.case("parse", exception=EgaugeParsingException, expected=ConfigEntryState.SETUP_ERROR),
)
async def setup_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: MagicMock = Depends(mock_egauge_client),
    *,
    exception: Exception,
    expected: ConfigEntryState,
) -> None:
    """Test setup with errors."""
    entry.add_to_hass(hass)
    client.get_device_serial_number.side_effect = exception

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(expected)
