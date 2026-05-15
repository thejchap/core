"""Tests for rainforest eagle sensors."""

from unittest.mock import Mock

from tryke import Depends, expect, fixture, test

from homeassistant.components.rainforest_eagle.const import DOMAIN
from homeassistant.core import HomeAssistant

from . import MOCK_200_RESPONSE_WITH_PRICE
from ._fixtures import (
    rainforest_translations,
    setup_rainforest_100,
    setup_rainforest_200,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _translations: None = Depends(rainforest_translations),
) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def sensors_200(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    rainforest: Mock = Depends(setup_rainforest_200),
) -> None:
    """Test the sensors."""
    expect(len(hass.states.async_all())).to_equal(3)

    demand = hass.states.get("sensor.eagle_200_power_demand")
    expect(demand is not None).to_be(True)
    expect(demand.state).to_equal("1.152000")
    expect(demand.attributes["unit_of_measurement"]).to_equal("kW")

    delivered = hass.states.get("sensor.eagle_200_total_energy_delivered")
    expect(delivered is not None).to_be(True)
    expect(delivered.state).to_equal("45251.285000")
    expect(delivered.attributes["unit_of_measurement"]).to_equal("kWh")

    received = hass.states.get("sensor.eagle_200_total_energy_received")
    expect(received is not None).to_be(True)
    expect(received.state).to_equal("232.232000")
    expect(received.attributes["unit_of_measurement"]).to_equal("kWh")

    rainforest.get_device_query.return_value = MOCK_200_RESPONSE_WITH_PRICE

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(4)

    price = hass.states.get("sensor.eagle_200_energy_price")
    expect(price is not None).to_be(True)
    expect(price.state).to_equal("0.053990")
    expect(price.attributes["unit_of_measurement"]).to_equal("USD/kWh")


@test
async def sensors_100(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _rainforest: Mock = Depends(setup_rainforest_100),
) -> None:
    """Test the sensors."""
    expect(len(hass.states.async_all())).to_equal(3)

    demand = hass.states.get("sensor.eagle_100_power_demand")
    expect(demand is not None).to_be(True)
    expect(demand.state).to_equal("1.152000")
    expect(demand.attributes["unit_of_measurement"]).to_equal("kW")

    delivered = hass.states.get("sensor.eagle_100_total_energy_delivered")
    expect(delivered is not None).to_be(True)
    expect(delivered.state).to_equal("45251.285000")
    expect(delivered.attributes["unit_of_measurement"]).to_equal("kWh")

    received = hass.states.get("sensor.eagle_100_total_energy_received")
    expect(received is not None).to_be(True)
    expect(received.state).to_equal("232.232000")
    expect(received.attributes["unit_of_measurement"]).to_equal("kWh")
