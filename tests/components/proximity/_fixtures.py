"""Tryke fixtures for Proximity tests."""

from __future__ import annotations

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture


@fixture
def config_zones(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Set up zones for test."""
    hass.config.components.add("zone")
    hass.states.async_set(
        "zone.home",
        "zoning",
        {"name": "Home", "latitude": 2.1, "longitude": 1.1, "radius": 10},
    )
    hass.states.async_set(
        "zone.work",
        "zoning",
        {"name": "Work", "latitude": 2.3, "longitude": 1.3, "radius": 10},
    )
