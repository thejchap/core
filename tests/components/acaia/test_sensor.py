"""Test sensors for acaia integration."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

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
from tests.hass_fixtures import (
    enable_bluetooth,
    freezer as freezer_fixture,
    hass as hass_fixture,
)


# Inject sensor entity_component translations so entity_id slugs include
# _battery, _weight, etc., matching what the test expects.
_FAKE_SENSOR_COMPONENT_TRANSLATIONS = {
    "component.sensor.entity_component.battery.name": "Battery",
    "component.sensor.entity_component.weight.name": "Weight",
    "component.sensor.entity_component.volume_flow_rate.name": "Volume flow rate",
}


async def _fake_get_translations(
    hass_arg, language, category, integrations=None, config_flow=None
):
    return _FAKE_SENSOR_COMPONENT_TRANSLATIONS


@fixture
def _trigger_executor(_bluetooth: None = Depends(enable_bluetooth)) -> None:
    """Force tryke to build a per-module HookExecutor and enable bluetooth."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensors() -> None:
    """Stub for test_sensors (snapshot-based)."""


@test
async def restore_state(
    _trigger: None = Depends(_trigger_executor),
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
                State(
                    entity_id,
                    "1",
                ),
                {
                    "native_value": 65,
                    "native_unit_of_measurement": PERCENTAGE,
                },
            ),
        ),
    )

    with patch(
        "homeassistant.helpers.entity_platform.translation.async_get_translations",
        side_effect=_fake_get_translations,
    ):
        await setup_integration(hass, mock_config_entry)

    state = hass.states.get(entity_id)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("65")


@test
async def battery_available_within_session_after_disconnect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_scale: MagicMock = Depends(mock_scale),
    freezer=Depends(freezer_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test battery stays available on disconnect when no restore data exists."""
    entity_id = "sensor.lunar_ddeeff_battery"

    with patch(
        "homeassistant.helpers.entity_platform.translation.async_get_translations",
        side_effect=_fake_get_translations,
    ):
        await setup_integration(hass, mock_config_entry)

    state = hass.states.get(entity_id)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("42")

    mock_scale.connected = False
    freezer.tick(timedelta(minutes=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("42")
