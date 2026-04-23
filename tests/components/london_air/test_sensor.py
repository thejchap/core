"""The tests for the london_air platform."""

from http import HTTPStatus

import requests_mock as requests_mock_lib
from tryke import Depends, expect, fixture, test

from homeassistant.components.london_air.sensor import CONF_LOCATIONS, URL
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import async_load_fixture
from tests.hass_fixtures import hass

VALID_CONFIG = {"sensor": {"platform": "london_air", CONF_LOCATIONS: ["Merton"]}}


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def valid_state(hass: HomeAssistant = Depends(hass)) -> None:
    """Test for operational london_air sensor with proper attributes."""
    with requests_mock_lib.Mocker() as requests_mock:
        requests_mock.get(
            URL,
            text=await async_load_fixture(hass, "london_air.json", "london_air"),
            status_code=HTTPStatus.OK,
        )
        result = await async_setup_component(hass, "sensor", VALID_CONFIG)
        expect(result).to_be(True)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.merton")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("Low")
    expect(state.attributes["icon"]).to_equal("mdi:cloud-outline")
    expect(state.attributes["updated"]).to_equal("2017-08-03 03:00:00")
    expect(state.attributes["sites"]).to_equal(2)
    expect(state.attributes["friendly_name"]).to_equal("Merton")

    sites = state.attributes["data"]
    expect(sites is not None).to_be(True)
    expect(len(sites)).to_equal(2)
    expect(sites[0]["site_code"]).to_equal("ME2")
    expect(sites[0]["site_type"]).to_equal("Roadside")
    expect(sites[0]["site_name"]).to_equal("Merton Road")
    expect(sites[0]["pollutants_status"]).to_equal("Low")

    pollutants = sites[0]["pollutants"]
    expect(pollutants is not None).to_be(True)
    expect(len(pollutants)).to_equal(1)
    expect(pollutants[0]["code"]).to_equal("PM10")
    expect(pollutants[0]["quality"]).to_equal("Low")
    expect(int(pollutants[0]["index"])).to_equal(2)
    expect(pollutants[0]["summary"]).to_equal("PM10 is Low")


@test
async def api_failure(hass: HomeAssistant = Depends(hass)) -> None:
    """Test for failure in the API."""
    with requests_mock_lib.Mocker() as requests_mock:
        requests_mock.get(URL, status_code=HTTPStatus.SERVICE_UNAVAILABLE)
        result = await async_setup_component(hass, "sensor", VALID_CONFIG)
        expect(result).to_be(True)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.merton")
    expect(state is not None).to_be(True)
    expect(state.attributes["updated"] is None).to_be(True)
    expect(state.attributes["sites"]).to_equal(0)
