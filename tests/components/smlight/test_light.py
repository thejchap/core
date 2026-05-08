"""Tests for SMLIGHT light entities."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry, mock_smlight_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


async def setup_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> MockConfigEntry:
    """Set up the integration."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Force tryke to fully resolve hass before each test."""


@test
async def light_not_created_non_ultima(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    smlight_client: MagicMock = Depends(mock_smlight_client),
) -> None:
    """Test light entity is not created for non-Ultima devices."""
    await setup_integration(hass, config_entry)

    state = hass.states.get("light.mock_title_ambilight")
    expect(state is None).to_be(True)


@test.skip("requires syrupy snapshot for ultima device")
async def light_setup_ultima() -> None:
    """Stub for test_light_setup_ultima (port deferred)."""

@test.skip("requires SSE event injection")
async def light_turn_on_off() -> None:
    """Stub for test_light_turn_on_off (port deferred)."""

@test.skip("requires SSE event injection")
async def light_brightness() -> None:
    """Stub for test_light_brightness (port deferred)."""

@test.skip("requires SSE event injection")
async def light_rgb_color() -> None:
    """Stub for test_light_rgb_color (port deferred)."""

@test.skip("requires SSE event injection")
async def light_effect() -> None:
    """Stub for test_light_effect (port deferred)."""

@test.skip("requires translation injection")
async def light_invalid_effect() -> None:
    """Stub for test_light_invalid_effect (port deferred)."""

@test.skip("requires SSE event injection")
async def light_turn_on_when_on_is_noop() -> None:
    """Stub for test_light_turn_on_when_on_is_noop (port deferred)."""

@test.skip("requires SSE event injection")
async def light_state_handles_invalid_attributes_from_sse() -> None:
    """Stub (port deferred)."""

@test.skip("requires translation injection")
async def ambilight_connection_error() -> None:
    """Stub for test_ambilight_connection_error (port deferred)."""
