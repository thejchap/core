"""Tryke fixtures for the History integration."""

from __future__ import annotations

from tryke import Depends, fixture

from homeassistant.components import history
from homeassistant.const import CONF_DOMAINS, CONF_ENTITIES, CONF_EXCLUDE, CONF_INCLUDE
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_recorder_mock


@fixture
async def recorder_mock(
    hass: HomeAssistant = Depends(hass_fixture),
):
    """Set up an in-memory recorder for history tests."""
    return await setup_recorder_mock(hass)


@fixture
async def hass_history(
    hass: HomeAssistant = Depends(hass_fixture),
    _recorder=Depends(recorder_mock),
) -> None:
    """Set up the history integration with include/exclude filters."""
    config = history.CONFIG_SCHEMA(
        {
            history.DOMAIN: {
                CONF_INCLUDE: {
                    CONF_DOMAINS: ["media_player"],
                    CONF_ENTITIES: ["thermostat.test"],
                },
                CONF_EXCLUDE: {
                    CONF_DOMAINS: ["thermostat"],
                    CONF_ENTITIES: ["media_player.test"],
                },
            }
        }
    )
    assert await async_setup_component(hass, history.DOMAIN, config)
