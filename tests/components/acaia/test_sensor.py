"""Test sensors for acaia integration."""

from datetime import timedelta
from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, State

from . import setup_integration
from ._fixtures import mock_config_entry, mock_scale

from tests.common import (
    MockConfigEntry,
    async_fire_time_changed,
    mock_restore_cache_with_extra_data,
)
from tests.hass_fixtures import freezer as freezer_fixture, hass as hass_fixture


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("uses syrupy snapshot")
async def sensors() -> None:
    """Test the Acaia sensors (snapshot platform)."""


@test
async def restore_state(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_scale: MagicMock = Depends(mock_scale),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test battery sensor restore state."""
    mock_scale.device_state = None
    entity_id = "sensor.lunar_ddeeff_battery"

    mock_restore_cache_with_extra_data(
        hass,
        (
            (
                State(entity_id, "1"),
                {
                    "native_value": 65,
                    "native_unit_of_measurement": PERCENTAGE,
                },
            ),
        ),
    )

    await setup_integration(hass, mock_config_entry)

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal("65")


@test
async def battery_available_within_session_after_disconnect(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_scale: MagicMock = Depends(mock_scale),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test battery stays available on disconnect when no restore data exists."""
    entity_id = "sensor.lunar_ddeeff_battery"

    await setup_integration(hass, mock_config_entry)

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal("42")

    mock_scale.connected = False
    freezer.tick(timedelta(minutes=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal("42")
