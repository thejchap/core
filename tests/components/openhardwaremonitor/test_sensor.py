"""The tests for the Open Hardware Monitor platform."""

from collections.abc import Generator

import requests_mock as requests_mock_lib
from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import async_load_fixture
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def requests_mocker() -> Generator[requests_mock_lib.Mocker]:
    """Provide a requests_mock.Mocker."""
    with requests_mock_lib.Mocker() as mock:
        yield mock


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock: requests_mock_lib.Mocker = Depends(requests_mocker),
) -> None:
    """Test for successfully setting up the platform."""
    config = {
        "sensor": {
            "platform": "openhardwaremonitor",
            "host": "localhost",
            "port": 8085,
        }
    }

    requests_mock.get(
        "http://localhost:8085/data.json",
        text=await async_load_fixture(
            hass, "openhardwaremonitor.json", "openhardwaremonitor"
        ),
    )

    await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()

    entities = hass.states.async_entity_ids("sensor")
    expect(len(entities)).to_equal(38)

    state = hass.states.get(
        "sensor.test_pc_intel_core_i7_7700_temperatures_cpu_core_1"
    )

    expect(state is not None).to_be(True)
    expect(state.state).to_equal("31.0")

    state = hass.states.get(
        "sensor.test_pc_intel_core_i7_7700_temperatures_cpu_core_2"
    )

    expect(state is not None).to_be(True)
    expect(state.state).to_equal("30.0")
