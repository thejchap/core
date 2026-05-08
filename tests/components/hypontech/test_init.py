"""Test the Hypontech Cloud init."""

from unittest.mock import AsyncMock

from hyponcloud import AuthenticationError, RequestError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_config_entry, mock_hyponcloud

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test.cases(
    test.case(
        "timeout",
        side_effect=TimeoutError,
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "auth_error",
        side_effect=AuthenticationError,
        expected_state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "request_error",
        side_effect=RequestError,
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def setup_entry(
    *,
    side_effect: type[Exception],
    expected_state: ConfigEntryState,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    hyponcloud: AsyncMock = Depends(mock_hyponcloud),
) -> None:
    """Test setup entry with various API errors."""
    hyponcloud.connect.side_effect = side_effect
    await setup_integration(hass, config_entry)

    expect(config_entry.state).to_be(expected_state)


@test
async def setup_and_unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    hyponcloud: AsyncMock = Depends(mock_hyponcloud),
) -> None:
    """Test setup and unload of config entry."""
    await setup_integration(hass, config_entry)

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
