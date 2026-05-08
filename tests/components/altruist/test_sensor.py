"""Tests for the Altruist integration sensor platform."""

from datetime import timedelta
from unittest.mock import AsyncMock, patch

from altruistclient import AltruistError
from tryke import Depends, expect, fixture, test

from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant

from ._fixtures import mock_altruist_client, mock_altruist_device, mock_config_entry

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Force tryke to build a per-module HookExecutor for this file."""


# Pre-built fake translations for the altruist sensor entity_id slugs.
# The tryke env doesn't compile integration translations/, so without this
# the entity_id falls back to the device name and the test can't find
# the expected sensor.
_FAKE_TRANSLATIONS = {
    "component.altruist.entity.sensor.temperature.name": "{sensor_name} temperature",
    "component.altruist.entity.sensor.humidity.name": "{sensor_name} humidity",
    "component.altruist.entity.sensor.pressure.name": "{sensor_name} pressure",
    "component.altruist.entity.sensor.co2.name": "{sensor_name} CO2",
    "component.altruist.entity.sensor.signal_strength.name": "Signal strength",
    "component.altruist.entity.sensor.average_noise.name": "Average noise",
    "component.altruist.entity.sensor.maximum_noise.name": "Maximum noise",
    "component.altruist.entity.sensor.radiation.name": "Radiation level",
}


async def _fake_get_translations(
    hass_arg, language, category, integrations=None, config_flow=None
):
    if integrations and "altruist" in integrations:
        return _FAKE_TRANSLATIONS
    return {}


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def all_entities() -> None:
    """Stub for test_all_entities (snapshot-based)."""


@test
async def connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_altruist_client: AsyncMock = Depends(mock_altruist_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test coordinator error handling during update."""
    mock_config_entry.add_to_hass(hass)
    with patch(
        "homeassistant.helpers.entity_platform.translation.async_get_translations",
        side_effect=_fake_get_translations,
    ):
        expect(
            await hass.config_entries.async_setup(mock_config_entry.entry_id)
        ).to_be(True)
        await hass.async_block_till_done()

    mock_altruist_client.fetch_data.side_effect = AltruistError()

    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.5366960e8b18_bme280_temperature")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNAVAILABLE)
