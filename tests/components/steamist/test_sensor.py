"""Tryke skip stub (pending port)."""

from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant

from . import (
    MOCK_ASYNC_GET_STATUS_ACTIVE,
    MOCK_ASYNC_GET_STATUS_INACTIVE,
    _async_setup_entry_with_status,
)
from ._fixtures import mock_aio_discovery

from tests.hass_fixtures import hass as hass_fixture, mock_network

_FAKE_TRANSLATIONS = {
    "component.steamist.entity.sensor.steam_temperature.name": "Steam temperature",
    "component.steamist.entity.sensor.steam_minutes_remain.name": "Steam minutes remain",
}


async def _fake_get_translations(
    hass, language, category, integrations=None, config_flow=None
):
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(hass, language, category, integration=None):
    return _FAKE_TRANSLATIONS


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test
async def steam_active(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_aio_discovery: MagicMock = Depends(mock_aio_discovery),
) -> None:
    """Test that the sensors are setup with the expected values when steam is active."""
    with (
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
    ):
        await _async_setup_entry_with_status(hass, MOCK_ASYNC_GET_STATUS_ACTIVE)
    state = hass.states.get("sensor.steam_temperature")
    expect(round(float(state.state))).to_equal(39)
    expect(state.attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal(
        UnitOfTemperature.CELSIUS
    )
    state = hass.states.get("sensor.steam_minutes_remain")
    expect(state.state).to_equal("14")
    expect(state.attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal(UnitOfTime.MINUTES)


@test
async def steam_inactive(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_aio_discovery: MagicMock = Depends(mock_aio_discovery),
) -> None:
    """Test that the sensors are setup with the expected values when steam is not active."""
    with (
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
    ):
        await _async_setup_entry_with_status(hass, MOCK_ASYNC_GET_STATUS_INACTIVE)
    state = hass.states.get("sensor.steam_temperature")
    expect(round(float(state.state))).to_equal(21)
    expect(state.attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal(
        UnitOfTemperature.CELSIUS
    )
    state = hass.states.get("sensor.steam_minutes_remain")
    expect(state.state).to_equal("0")
    expect(state.attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal(UnitOfTime.MINUTES)


_ = (mock_aio_discovery,)
