"""Test the Homevolt init module."""

from unittest.mock import MagicMock

from homevolt import HomevoltAuthenticationError, HomevoltConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry, mock_homevolt_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def load_unload_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_homevolt_client: MagicMock = Depends(mock_homevolt_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test load and unload entry."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
    mock_homevolt_client.close_connection.assert_called_once()


@test.cases(
    test.case(
        "connection_error",
        side_effect=HomevoltConnectionError("Connection failed"),
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "auth_error",
        side_effect=HomevoltAuthenticationError("Authentication failed"),
        expected_state=ConfigEntryState.SETUP_ERROR,
    ),
)
async def config_entry_setup_failure(
    *,
    side_effect: Exception,
    expected_state: ConfigEntryState,
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_homevolt_client: MagicMock = Depends(mock_homevolt_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the Homevolt configuration entry setup failures."""
    mock_homevolt_client.update_info.side_effect = side_effect
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    expect(mock_config_entry.state).to_be(expected_state)
