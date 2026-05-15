"""Test setting up sensors."""

from datetime import timedelta
from unittest.mock import MagicMock

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.components.sensor import (
    ATTR_STATE_CLASS,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_FRIENDLY_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import INPUT_SENSOR, OUTPUT_SENSOR
from ._fixtures import mock_iotawatt as mock_iotawatt_fixture

from tests.common import async_fire_time_changed
from tests.hass_fixtures import (
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def sensor_type_input(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    mock_iotawatt: MagicMock = Depends(mock_iotawatt_fixture),
) -> None:
    """Test input sensors work."""
    expect(bool(await async_setup_component(hass, "iotawatt", {}))).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_entity_ids())).to_equal(0)

    # Discover this sensor during a regular update.
    mock_iotawatt.getSensors.return_value["sensors"]["my_sensor_key"] = INPUT_SENSOR
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(len(hass.states.async_entity_ids())).to_equal(1)
    state = hass.states.get("sensor.test_device_my_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("23")
    expect(state.attributes[ATTR_STATE_CLASS] is SensorStateClass.MEASUREMENT).to_be(
        True
    )
    expect(state.attributes[ATTR_FRIENDLY_NAME]).to_equal("Test Device My Sensor")
    expect(state.attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal(UnitOfPower.WATT)
    expect(state.attributes[ATTR_DEVICE_CLASS]).to_equal(SensorDeviceClass.POWER)
    expect(state.attributes["channel"]).to_equal("1")
    expect(state.attributes["type"]).to_equal("Input")

    mock_iotawatt.getSensors.return_value["sensors"].pop("my_sensor_key")
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(hass.states.get("sensor.test_device_my_sensor") is None).to_be(True)


@test
async def sensor_type_output(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    mock_iotawatt: MagicMock = Depends(mock_iotawatt_fixture),
) -> None:
    """Tests the sensor type of Output."""
    mock_iotawatt.getSensors.return_value["sensors"]["my_watthour_sensor_key"] = (
        OUTPUT_SENSOR
    )
    expect(bool(await async_setup_component(hass, "iotawatt", {}))).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_entity_ids())).to_equal(1)

    state = hass.states.get("sensor.my_watthour_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("243")
    expect(state.attributes[ATTR_STATE_CLASS] is SensorStateClass.TOTAL).to_be(True)
    expect(state.attributes[ATTR_FRIENDLY_NAME]).to_equal("My WattHour Sensor")
    expect(state.attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal(UnitOfEnergy.WATT_HOUR)
    expect(state.attributes[ATTR_DEVICE_CLASS]).to_equal(SensorDeviceClass.ENERGY)
    expect(state.attributes["type"]).to_equal("Output")

    mock_iotawatt.getSensors.return_value["sensors"].pop("my_watthour_sensor_key")
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(hass.states.get("sensor.my_watthour_sensor") is None).to_be(True)
