"""Tests for the Roku select platform."""

from unittest.mock import MagicMock

from rokuecp import (
    Application,
    Device as RokuDevice,
    RokuConnectionError,
    RokuConnectionTimeoutError,
    RokuError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.roku.const import DOMAIN
from homeassistant.components.roku.coordinator import SCAN_INTERVAL
from homeassistant.components.select import (
    ATTR_OPTION,
    ATTR_OPTIONS,
    DOMAIN as SELECT_DOMAIN,
)
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_SELECT_OPTION
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from ._fixtures import mock_config_entry, mock_device, mock_roku

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def application_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    device: RokuDevice = Depends(mock_device),
    roku: MagicMock = Depends(mock_roku),
) -> None:
    """Test the creation and values of the Roku selects."""
    entity_registry.async_get_or_create(
        SELECT_DOMAIN,
        DOMAIN,
        "1GU48T017973_application",
        suggested_object_id="my_roku_3_application",
        disabled_by=None,
    )

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("select.my_roku_3_application")
    expect(state).not_.to_be(None)
    expect(state.attributes.get(ATTR_OPTIONS)).to_equal(
        [
            "Home",
            "Amazon Video on Demand",
            "Free FrameChannel Service",
            "MLB.TV" + "®",
            "Mediafly",
            "Netflix",
            "Pandora",
            "Pluto TV - It's Free TV",
            "Roku Channel Store",
        ]
    )
    expect(state.state).to_equal("Home")

    entry = entity_registry.async_get("select.my_roku_3_application")
    expect(entry).not_.to_be(None)
    expect(entry.unique_id).to_equal("1GU48T017973_application")

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: "select.my_roku_3_application",
            ATTR_OPTION: "Netflix",
        },
        blocking=True,
    )

    expect(roku.launch.call_count).to_equal(1)
    roku.launch.assert_called_with("12")
    device.app = device.apps[1]

    async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL)
    await hass.async_block_till_done()

    state = hass.states.get("select.my_roku_3_application")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal("Netflix")

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: "select.my_roku_3_application",
            ATTR_OPTION: "Home",
        },
        blocking=True,
    )

    expect(roku.remote.call_count).to_equal(1)
    roku.remote.assert_called_with("home")
    device.app = Application(
        app_id=None, name="Roku", version=None, screensaver=None
    )
    async_fire_time_changed(hass, dt_util.utcnow() + (SCAN_INTERVAL * 2))
    await hass.async_block_till_done()

    state = hass.states.get("select.my_roku_3_application")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal("Home")


@test.cases(
    test.case(
        "connection_error",
        error=RokuConnectionError,
        error_string="Error communicating with Roku API",
    ),
    test.case(
        "timeout_error",
        error=RokuConnectionTimeoutError,
        error_string="Timeout communicating with Roku API",
    ),
    test.case(
        "generic_error",
        error=RokuError,
        error_string="Invalid response from Roku API",
    ),
)
async def application_select_error(
    error: type[RokuError],
    error_string: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    roku: MagicMock = Depends(mock_roku),
) -> None:
    """Test error handling of the Roku selects."""
    entity_registry.async_get_or_create(
        SELECT_DOMAIN,
        DOMAIN,
        "1GU48T017973_application",
        suggested_object_id="my_roku_3_application",
        disabled_by=None,
    )

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    roku.launch.side_effect = error

    raised: HomeAssistantError | None = None
    try:
        await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {
                ATTR_ENTITY_ID: "select.my_roku_3_application",
                ATTR_OPTION: "Netflix",
            },
            blocking=True,
        )
    except HomeAssistantError as exc:
        raised = exc

    expect(raised).not_.to_be(None)
    expect(error_string in str(raised)).to_be(True)

    state = hass.states.get("select.my_roku_3_application")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal("Home")
    expect(roku.launch.call_count).to_equal(1)
    roku.launch.assert_called_with("12")


@test.skip("indirect parametrize selects rokutv fixture — needs init_integration_rokutv variant")
async def channel_state() -> None:
    """Stub for test_channel_state (port deferred)."""


@test.skip("indirect parametrize selects rokutv fixture — needs init_integration_rokutv variant")
async def channel_select_error() -> None:
    """Stub for test_channel_select_error (port deferred)."""
