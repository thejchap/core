"""Tests for the Firefly III integration."""

from unittest.mock import AsyncMock

from pyfirefly.exceptions import (
    FireflyAuthenticationError,
    FireflyConnectionError,
    FireflyTimeoutError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_config_entry, mock_firefly_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test.cases(
    test.case(
        "auth",
        exception=FireflyAuthenticationError("bad creds"),
        expected_state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "connection",
        exception=FireflyConnectionError("cannot connect"),
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "timeout",
        exception=FireflyTimeoutError("timeout"),
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def setup_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_firefly_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    exception: Exception,
    expected_state: ConfigEntryState,
) -> None:
    """Test the _async_setup."""
    client.get_about.side_effect = exception
    await setup_integration(hass, entry)
    expect(entry.state).to_be(expected_state)
