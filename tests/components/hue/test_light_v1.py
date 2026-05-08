"""Philips Hue lights platform tests."""

from unittest.mock import Mock

from tryke import Depends, expect, fixture, test

from homeassistant.components import hue
from homeassistant.components.hue.const import CONF_ALLOW_HUE_GROUPS
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from ._fixtures import mock_bridge_v1, no_request_delay
from .conftest import create_config_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level fixture anchor."""


async def _setup_bridge(hass: HomeAssistant, mock_bridge_v1: Mock) -> None:
    """Load the Hue light platform with the provided bridge."""
    hass.config.components.add(hue.DOMAIN)
    config_entry = create_config_entry()
    config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        config_entry, options={CONF_ALLOW_HUE_GROUPS: True}
    )
    config_entry.mock_state(hass, ConfigEntryState.LOADED)
    mock_bridge_v1.config_entry = config_entry
    config_entry.runtime_data = mock_bridge_v1
    await hass.config_entries.async_forward_entry_setups(
        config_entry, [Platform.LIGHT]
    )
    await hass.async_block_till_done()


@test
async def no_lights_or_groups(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_bridge_v1: Mock = Depends(mock_bridge_v1),
) -> None:
    """Test the update_lights function when no lights are found."""
    mock_bridge_v1.mock_light_responses.append({})
    mock_bridge_v1.mock_group_responses.append({})
    await _setup_bridge(hass, mock_bridge_v1)
    expect(len(mock_bridge_v1.mock_requests)).to_equal(2)
    expect(len(hass.states.async_all())).to_equal(0)


@test.skip("port deferred - sibling test")
async def not_load_groups_if_old_bridge() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def lights() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def lights_color_mode() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def groups() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def new_group_discovered() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def new_light_discovered() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def group_removed() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def light_removed() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def other_group_update() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def other_light_update() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def update_timeout() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def update_unauthorized() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def light_turn_on_service() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def light_turn_off_service() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def available() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def hs_color() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def group_features() -> None:
    """Stub."""
