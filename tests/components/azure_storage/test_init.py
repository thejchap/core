"""Test the Azure storage integration."""

from unittest.mock import MagicMock

from azure.core.exceptions import (
    ClientAuthenticationError,
    HttpResponseError,
    ResourceNotFoundError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_client, mock_config_entry

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
async def load_unload_config_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(mock_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test loading and unloading the integration."""
    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case(
        "auth_error",
        exception=ClientAuthenticationError,
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "http_error",
        exception=HttpResponseError,
        state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "not_found",
        exception=ResourceNotFoundError,
        state=ConfigEntryState.SETUP_ERROR,
    ),
)
async def setup_errors(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_client: MagicMock = Depends(mock_client),
    *,
    exception: Exception,
    state: ConfigEntryState,
) -> None:
    """Test various setup errors."""
    mock_client.exists.side_effect = exception()
    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(state)
