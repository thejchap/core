"""The test for the version binary sensor platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.version.const import DEFAULT_CONFIGURATION
from homeassistant.core import HomeAssistant

from .common import setup_version_integration

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def version_binary_sensor_local_source(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the Version binary sensor with local source."""
    await setup_version_integration(hass)

    state = hass.states.get(
        "binary_sensor.home_assistant_version_local_installation_update_available"
    )
    expect(state).to_be_falsy()


@test
async def version_binary_sensor(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the Version binary sensor."""
    await setup_version_integration(hass, {**DEFAULT_CONFIGURATION, "source": "pypi"})

    state = hass.states.get(
        "binary_sensor.home_assistant_version_local_installation_update_available"
    )
    expect(state).not_.to_be(None)
