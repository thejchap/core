"""The tests for the geolocation component."""

from tryke import Depends, expect, fixture, test

from homeassistant.components import geo_location
from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def setup_component(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Simple test setup of component."""
    result = await async_setup_component(hass, geo_location.DOMAIN, {})
    expect(bool(result)).to_be(True)


@test
async def event(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Simple test of the geolocation event class."""
    entity = GeolocationEvent()

    expect(entity.state).to_be(None)
    expect(entity.distance).to_be(None)
    expect(entity.latitude).to_be(None)
    expect(entity.longitude).to_be(None)
    expect(lambda: entity.source).to_raise(AttributeError)
