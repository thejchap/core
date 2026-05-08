"""Test the initialization of Yardian."""

from unittest.mock import AsyncMock

from pyyardian import NetworkException, NotAuthorizedException
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_config_entry, mock_yardian_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-local anchor fixture (tryke discovery quirk)."""


@test.cases(
    test.case(
        "not_authorized",
        exception=NotAuthorizedException,
        entry_state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "timeout",
        exception=TimeoutError,
        entry_state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "network",
        exception=NetworkException,
        entry_state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "generic",
        exception=Exception,
        entry_state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def setup_unauthorized(
    *,
    exception: type[Exception],
    entry_state: ConfigEntryState,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    yardian_client: AsyncMock = Depends(mock_yardian_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test setup when unauthorized."""
    yardian_client.fetch_device_state.side_effect = exception

    await setup_integration(hass, config_entry)

    expect(config_entry.state).to_be(entry_state)
