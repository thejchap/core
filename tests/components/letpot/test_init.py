"""Test the LetPot integration initialization and setup."""

from unittest.mock import MagicMock

from freezegun import freeze_time
from letpot.exceptions import (
    LetPotAuthenticationException,
    LetPotConnectionException,
    LetPotException,
)
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import (
    mock_client as mock_client_fixture,
    mock_config_entry as mock_config_entry_fixture,
    mock_device_client as mock_device_client_fixture,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def load_unload_config_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_client: MagicMock = Depends(mock_client_fixture),
    mock_device_client: MagicMock = Depends(mock_device_client_fixture),
) -> None:
    """Test config entry loading/unloading."""
    with freeze_time("2025-01-31 00:00:00"):
        await setup_integration(hass, mock_config_entry)

        expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
        mock_client.refresh_token.assert_not_called()
        mock_client.get_devices.assert_called_once()
        mock_device_client.subscribe.assert_called_once()
        mock_device_client.get_current_status.assert_called_once()

        await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
        mock_device_client.unsubscribe.assert_called_once()


@test
async def refresh_authentication_on_load(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_client: MagicMock = Depends(mock_client_fixture),
    mock_device_client: MagicMock = Depends(mock_device_client_fixture),
) -> None:
    """Test expired access token refreshed when needed to load config entry."""
    with freeze_time("2025-02-15 00:00:00"):
        await setup_integration(hass, mock_config_entry)

        expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
        mock_client.refresh_token.assert_called_once()

        mock_client.get_devices.assert_called_once()
        mock_device_client.subscribe.assert_called_once()
        mock_device_client.get_current_status.assert_called_once()


@test
async def refresh_token_error_aborts(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_client: MagicMock = Depends(mock_client_fixture),
) -> None:
    """Test expired refresh token aborting config entry loading."""
    with freeze_time("2025-03-01 00:00:00"):
        mock_client.refresh_token.side_effect = LetPotAuthenticationException

        await setup_integration(hass, mock_config_entry)

        expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
        mock_client.refresh_token.assert_called_once()
        mock_client.get_devices.assert_not_called()


@test.cases(
    test.case(
        "auth_exception",
        exception=LetPotAuthenticationException,
        config_entry_state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "connection_exception",
        exception=LetPotConnectionException,
        config_entry_state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def get_devices_exceptions(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_client: MagicMock = Depends(mock_client_fixture),
    mock_device_client: MagicMock = Depends(mock_device_client_fixture),
    *,
    exception: type[Exception],
    config_entry_state: ConfigEntryState,
) -> None:
    """Test config entry errors if an exception is raised when getting devices."""
    mock_client.get_devices.side_effect = exception

    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(config_entry_state)
    mock_client.get_devices.assert_called_once()
    mock_device_client.subscribe.assert_not_called()


@test
async def device_subscribe_authentication_exception(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    _client: MagicMock = Depends(mock_client_fixture),
    mock_device_client: MagicMock = Depends(mock_device_client_fixture),
) -> None:
    """Test config entry errors if it is not allowed to subscribe to device updates."""
    mock_device_client.subscribe.side_effect = LetPotAuthenticationException

    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
    mock_device_client.subscribe.assert_called_once()
    mock_device_client.get_current_status.assert_not_called()


@test
async def device_refresh_exception(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    _client: MagicMock = Depends(mock_client_fixture),
    mock_device_client: MagicMock = Depends(mock_device_client_fixture),
) -> None:
    """Test config entry errors with retry if getting a device state update fails."""
    mock_device_client.get_current_status.side_effect = LetPotException

    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
    mock_device_client.get_current_status.assert_called_once()
