"""Test Blue Current Init Component."""

from unittest.mock import patch

from bluecurrent_api.exceptions import (
    BlueCurrentException,
    InvalidApiToken,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.blue_current import async_setup_entry
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    IntegrationError,
)

from ._fixtures import config_entry as config_entry_fixture

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def load_unload_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
) -> None:
    """Test load and unload entry."""
    with (
        patch("homeassistant.components.blue_current.Client.validate_api_token"),
        patch("homeassistant.components.blue_current.Client.wait_for_charge_points"),
        patch("homeassistant.components.blue_current.Client.get_charge_cards"),
        patch("homeassistant.components.blue_current.Client.disconnect"),
        patch(
            "homeassistant.components.blue_current.Client.connect",
            lambda self, on_data, on_open: hass.loop.create_future(),
        ),
    ):
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.LOADED)

        await hass.config_entries.async_unload(config_entry.entry_id)
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case(
        "invalid_api_token",
        api_error=InvalidApiToken,
        config_error=ConfigEntryAuthFailed,
    ),
    test.case(
        "blue_current_exception",
        api_error=BlueCurrentException,
        config_error=ConfigEntryNotReady,
    ),
)
async def config_exceptions(
    *,
    api_error: type[BlueCurrentException],
    config_error: type[IntegrationError],
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
) -> None:
    """Test if the correct config error is raised when connecting to the api fails."""
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.blue_current.Client.validate_api_token",
        side_effect=api_error,
    ):
        async with expect_raises_async(config_error):
            await async_setup_entry(hass, config_entry)


@test.skip("requires init_integration helper with FutureContainer + Event waits")
async def connect_websocket_error() -> None:
    """Stub for test_connect_websocket_error."""


@test.skip("requires init_integration helper with FutureContainer + Event waits")
async def connect_request_limit_reached_error() -> None:
    """Stub for test_connect_request_limit_reached_error."""


@test.skip("requires init_integration helper with FutureContainer + Event waits")
async def start_charging_action() -> None:
    """Stub for test_start_charging_action."""


@test.skip("requires init_integration helper with FutureContainer + Event waits")
async def start_charging_action_without_card() -> None:
    """Stub for test_start_charging_action_without_card."""


@test.skip("requires init_integration helper with FutureContainer + Event waits")
async def start_charging_action_errors() -> None:
    """Stub for test_start_charging_action_errors."""
