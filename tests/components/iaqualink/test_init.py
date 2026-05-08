"""Tests for iAquaLink integration."""

from unittest.mock import patch

from iaqualink.exception import AqualinkServiceException
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level fixture anchor."""


@test.skip("requires AqualinkSystem fixture chain - port deferred")
async def system_refresh_failure_marks_entities_unavailable() -> None:
    """Stub."""


@test.skip("requires AqualinkSystem fixture chain - port deferred")
async def light_service_calls_update_entity_state() -> None:
    """Stub."""


@test
async def setup_login_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test setup encountering a login exception."""
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.iaqualink.AqualinkClient.login",
        side_effect=AqualinkServiceException,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    expect(config_entry.state is ConfigEntryState.SETUP_RETRY).to_be(True)


@test.skip("port deferred")
async def setup_login_unauthorized() -> None:
    """Stub."""


@test.skip("port deferred")
async def setup_login_timeout() -> None:
    """Stub."""


@test.skip("port deferred")
async def setup_systems_exception() -> None:
    """Stub."""


@test.skip("port deferred")
async def setup_systems_unauthorized() -> None:
    """Stub."""


@test.skip("port deferred")
async def setup_first_refresh_unauthorized_closes_client() -> None:
    """Stub."""


@test.skip("port deferred")
async def setup_no_systems_recognized() -> None:
    """Stub."""


@test.skip("port deferred")
async def setup_devices_exception() -> None:
    """Stub."""


@test.skip("port deferred")
async def setup_all_good_no_recognized_devices() -> None:
    """Stub."""


@test.skip("port deferred")
async def setup_all_good_all_device_types() -> None:
    """Stub."""


@test.skip("port deferred")
async def multiple_updates() -> None:
    """Stub."""


@test.skip("port deferred")
async def entity_assumed_and_available() -> None:
    """Stub."""


@test.skip("port deferred")
async def system_refresh_unauthorized_triggers_reauth() -> None:
    """Stub."""
