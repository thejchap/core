"""Test Autoskope integration setup."""

from unittest.mock import AsyncMock

from autoskope_client.models import CannotConnect, InvalidAuth
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_autoskope_client, mock_config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def setup_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_autoskope_client),
) -> None:
    """Test successful setup and unload of entry."""
    await setup_integration(hass, mock_config_entry)
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case(
        "invalid_auth",
        exception=InvalidAuth("Invalid credentials"),
        expected_state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "cannot_connect",
        exception=CannotConnect("Connection failed"),
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def setup_entry_errors(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_autoskope_client: AsyncMock = Depends(mock_autoskope_client),
    *,
    exception: Exception,
    expected_state: ConfigEntryState,
) -> None:
    """Test setup with authentication and connection errors."""
    mock_autoskope_client.connect.side_effect = exception

    await setup_integration(hass, mock_config_entry)
    expect(mock_config_entry.state).to_be(expected_state)
