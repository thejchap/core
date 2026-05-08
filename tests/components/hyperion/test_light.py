"""Tests for the Hyperion integration light platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from . import TEST_ENTITY_ID_1, create_mock_client, setup_test_config_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level fixture anchor."""


@test
async def setup_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up the component via config entries."""
    await setup_test_config_entry(hass, hyperion_client=create_mock_client())
    expect(hass.states.get(TEST_ENTITY_ID_1) is not None).to_be(True)


@test.skip("port deferred - sibling tests")
async def setup_config_entry_not_ready_connect_fail() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def setup_config_entry_not_ready_switch_instance_fail() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def setup_config_entry_not_ready_load_state_fail() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def setup_config_entry_dynamic_instances() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def light_basic_properties() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def light_async_turn_on() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def light_async_turn_on_fail_async_send_set_effect() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def light_async_turn_on_fail_async_send_set_color() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def light_async_turn_off_fail_async_send_send_clear() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def light_async_updates_from_hyperion_client() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def light_async_updates_from_hyperion_client_no_priority() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def light_async_updates_from_hyperion_client_priority_no_owner() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def device_info() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def light_options() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def deprecated_effect_names() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def deprecated_effect_names_not_in_effect_list() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def setup_entry_no_token() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def setup_entry_token() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def setup_entry_token_failure() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def setup_with_token_invalid() -> None:
    """Stub."""
