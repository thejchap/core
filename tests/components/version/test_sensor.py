"""The test for the version sensor platform."""

from freezegun.api import FrozenDateTimeFactory
from pyhaversion.exceptions import HaVersionException
from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from .common import MOCK_VERSION, mock_get_version_update, setup_version_integration

from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def version_sensor(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test the Version sensor with different sources."""
    await setup_version_integration(hass)

    state = hass.states.get("sensor.home_assistant_version_local_installation")
    expect(state.state).to_equal(MOCK_VERSION)
    expect("source" in state.attributes).to_be(False)
    expect("channel" in state.attributes).to_be(False)


@test
async def update(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test updates."""
    await setup_version_integration(hass)
    expect(
        hass.states.get("sensor.home_assistant_version_local_installation").state
    ).to_equal(MOCK_VERSION)

    await mock_get_version_update(hass, freezer, version="1970.1.1")
    expect(
        hass.states.get("sensor.home_assistant_version_local_installation").state
    ).to_equal("1970.1.1")

    expect("Error fetching version data" in caplog.text).to_be(False)
    await mock_get_version_update(hass, freezer, side_effect=HaVersionException)
    expect(
        hass.states.get("sensor.home_assistant_version_local_installation").state
    ).to_equal("unavailable")
    expect("Error fetching version data" in caplog.text).to_be(True)
