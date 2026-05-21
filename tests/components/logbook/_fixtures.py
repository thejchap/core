"""Tryke fixtures for the logbook integration."""

from __future__ import annotations

from tryke import Depends, fixture

from homeassistant.components import logbook
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_recorder_mock

EMPTY_CONFIG = logbook.CONFIG_SCHEMA({logbook.DOMAIN: {}})


@fixture
async def recorder_mock(
    hass: HomeAssistant = Depends(hass_fixture),
):
    """Set up an in-memory recorder for logbook tests."""
    return await setup_recorder_mock(hass)


@fixture
async def hass_(
    hass: HomeAssistant = Depends(hass_fixture),
    _recorder=Depends(recorder_mock),
) -> HomeAssistant:
    """Set up the logbook integration."""
    assert await async_setup_component(hass, logbook.DOMAIN, EMPTY_CONFIG)
    return hass


@fixture
async def set_utc(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set timezone to UTC."""
    await hass.config.async_set_time_zone("UTC")
