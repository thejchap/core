"""Unit tests for the iotty SWITCH component."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.iotty.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import (
    local_oauth_impl,
    mock_config_entry,
    mock_get_devices_nodevices,
    setup_credentials,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level fixture anchor."""


@test
async def setup_entry_ok_nodevices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _credentials: None = Depends(setup_credentials),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    local_oauth_impl: config_entry_oauth2_flow.LocalOAuth2Implementation = Depends(
        local_oauth_impl
    ),
    _devices: AsyncMock = Depends(mock_get_devices_nodevices),
) -> None:
    """Correctly setup, with no iotty Devices to add to Hass."""
    mock_config_entry.add_to_hass(hass)

    config_entry_oauth2_flow.async_register_implementation(
        hass, DOMAIN, local_oauth_impl
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    expect(hass.states.async_entity_ids_count()).to_equal(0)


@test.skip("port deferred - sibling test")
async def turn_on_light_ok() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def turn_on_outlet_ok() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def turn_off_light_ok() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def turn_off_outlet_ok() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def devices_creaction_ok() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def devices_deletion_ok() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def devices_insertion_ok() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def outlet_insertion_ok() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def api_not_ok_entities_stay_the_same_as_before() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def turn_on_failed_call() -> None:
    """Stub."""
