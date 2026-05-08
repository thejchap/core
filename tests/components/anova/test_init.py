"""Test init for Anova."""

from unittest.mock import patch

from anova_wifi import AnovaApi
from tryke import Depends, expect, fixture, test

from homeassistant.components.anova.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_DEVICES, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from . import async_init_integration, create_entry
from ._fixtures import (
    anova_api,
    anova_api_no_devices,
    anova_api_websocket_failure,
    anova_api_wrong_login,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import mock_async_zeroconf


_FAKE_TRANSLATIONS = {
    "component.anova.entity.sensor.cook_time.name": "Cook time",
    "component.anova.entity.sensor.cook_time_remaining.name": "Cook time remaining",
    "component.anova.entity.sensor.heater_temperature.name": "Heater temperature",
    "component.anova.entity.sensor.mode.name": "Mode",
    "component.anova.entity.sensor.state.name": "State",
    "component.anova.entity.sensor.target_temperature.name": "Target temperature",
    "component.anova.entity.sensor.triac_temperature.name": "Triac temperature",
    "component.anova.entity.sensor.water_temperature.name": "Water temperature",
}


async def _fake_get_translations(
    hass, language, category, integrations=None, config_flow=None
):
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(hass, language, category, integration=None):
    return _FAKE_TRANSLATIONS


def _patch_translations():
    return (
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
    )


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zc: None = Depends(mock_async_zeroconf),
) -> None:
    """Per-module trigger to anchor fixture resolution."""


@test
async def async_setup_entry(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    anova_api: AnovaApi = Depends(anova_api),
) -> None:
    """Test a successful setup entry."""
    p1, p2 = _patch_translations()
    with p1, p2:
        await async_init_integration(hass)
    state = hass.states.get("sensor.anova_precision_cooker_mode")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal("idle")


@test
async def wrong_login(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    anova_api_wrong_login: AnovaApi = Depends(anova_api_wrong_login),
) -> None:
    """Test for setup failure if connection to Anova is missing."""
    entry = create_entry(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def unload_entry(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    anova_api: AnovaApi = Depends(anova_api),
) -> None:
    """Test successful unload of entry."""
    entry = await async_init_integration(hass)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def no_devices_found(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    anova_api_no_devices: AnovaApi = Depends(anova_api_no_devices),
) -> None:
    """Test when there don't seem to be any devices on the account."""
    entry = await async_init_integration(hass)
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def websocket_failure(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    anova_api_websocket_failure: AnovaApi = Depends(anova_api_websocket_failure),
) -> None:
    """Test that we successfully handle a websocket failure on setup."""
    entry = await async_init_integration(hass)
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def migration_removing_devices_in_config_entry(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    anova_api: AnovaApi = Depends(anova_api),
) -> None:
    """Test a successful setup entry with config entry migration."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Anova",
        data={
            CONF_USERNAME: "sample@gmail.com",
            CONF_PASSWORD: "sample",
            CONF_DEVICES: [],
        },
        unique_id="sample@gmail.com",
        version=1,
        minor_version=1,
    )
    entry.add_to_hass(hass)

    p1, p2 = _patch_translations()
    with p1, p2, patch("homeassistant.components.anova.AnovaApi.authenticate"):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.anova_precision_cooker_mode")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal("idle")

    expect(entry.version).to_equal(1)
    expect(entry.minor_version).to_equal(2)
    expect(CONF_DEVICES not in entry.data).to_be(True)
