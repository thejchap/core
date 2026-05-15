"""The test for the Trafikverket sensor platform."""

from datetime import timedelta
from unittest.mock import patch

from pytrafikverket.models import FerryStopModel
from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.components.trafikverket_ferry._fixtures import get_ferries, load_int
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def sensor(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    load_int: MockConfigEntry = Depends(load_int),
    get_ferries: list[FerryStopModel] = Depends(get_ferries),
) -> None:
    """Test the Trafikverket Ferry sensor."""
    state1 = hass.states.get("sensor.harbor1_departure_from")
    state2 = hass.states.get("sensor.harbor1_departure_to")
    state3 = hass.states.get("sensor.harbor1_departure_time")
    expect(state1.state).to_equal("Harbor 1")
    expect(state2.state).to_equal("Harbor 2")
    expect(state3.state).to_equal(str(dt_util.now().year + 1) + "-05-01T12:00:00+00:00")
    expect(state1.attributes["other_information"]).to_equal([""])

    get_ferries[0].other_information = ["Nothing exiting"]

    with patch(
        "homeassistant.components.trafikverket_ferry.coordinator.TrafikverketFerry.async_get_next_ferry_stops",
        return_value=get_ferries,
    ):
        async_fire_time_changed(
            hass,
            dt_util.utcnow() + timedelta(minutes=6),
        )
        await hass.async_block_till_done()

    state1 = hass.states.get("sensor.harbor1_departure_from")
    expect(state1.state).to_equal("Harbor 1")
    expect(state1.attributes["other_information"]).to_equal(["Nothing exiting"])
