"""Test different accessory types: Sensors (tryke port)."""

from __future__ import annotations

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.homekit import get_accessory
from homeassistant.components.homekit.accessories import HomeDriver
from homeassistant.components.homekit.const import (
    CONF_THRESHOLD_CO,
    CONF_THRESHOLD_CO2,
    PROP_CELSIUS,
    THRESHOLD_CO,
    THRESHOLD_CO2,
)
from homeassistant.components.homekit.type_sensors import (
    BINARY_SENSOR_SERVICE_MAP,
    AirQualitySensor,
    BinarySensor,
    CarbonDioxideSensor,
    CarbonMonoxideSensor,
    HumiditySensor,
    LightSensor,
    NitrogenDioxideSensor,
    PM10Sensor,
    PM25Sensor,
    TemperatureSensor,
    VolatileOrganicCompoundsSensor,
)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    EVENT_HOMEASSISTANT_START,
    PERCENTAGE,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.components.homekit._fixtures import hk_driver as hk_driver_fixture
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (see PATTERNS.md)."""
    return hass


@test
async def temperature(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "sensor.temperature"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = TemperatureSensor(hass, hk_driver, "Temperature", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    expect(acc.aid).to_equal(2)
    expect(acc.category).to_equal(10)  # Sensor

    expect(acc.char_temp.value).to_equal(0.0)
    for key, value in PROP_CELSIUS.items():
        expect(acc.char_temp.properties[key]).to_equal(value)

    hass.states.async_set(
        entity_id, STATE_UNKNOWN, {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS}
    )
    await hass.async_block_till_done()
    expect(acc.char_temp.value).to_equal(0.0)

    hass.states.async_set(
        entity_id, "20", {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS}
    )
    await hass.async_block_till_done()
    expect(acc.char_temp.value).to_equal(20)

    hass.states.async_set(
        entity_id, "0", {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS}
    )
    await hass.async_block_till_done()
    expect(acc.char_temp.value).to_equal(0)

    # The UOM changes, the accessory should reload itself
    with patch.object(acc, "async_reload") as mock_reload:
        hass.states.async_set(
            entity_id,
            "75.2",
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT},
        )
        await hass.async_block_till_done()
        expect(mock_reload.called).to_be(True)


@test
async def humidity(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "sensor.humidity"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = HumiditySensor(hass, hk_driver, "Humidity", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    expect(acc.aid).to_equal(2)
    expect(acc.category).to_equal(10)

    expect(acc.char_humidity.value).to_equal(0)

    hass.states.async_set(entity_id, STATE_UNKNOWN)
    await hass.async_block_till_done()
    expect(acc.char_humidity.value).to_equal(0)

    hass.states.async_set(entity_id, "20")
    await hass.async_block_till_done()
    expect(acc.char_humidity.value).to_equal(20)

    hass.states.async_set(entity_id, "0")
    await hass.async_block_till_done()
    expect(acc.char_humidity.value).to_equal(0)


@test
async def air_quality(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "sensor.air_quality"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = AirQualitySensor(hass, hk_driver, "Air Quality", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    expect(acc.aid).to_equal(2)
    expect(acc.category).to_equal(10)

    expect(acc.char_density.value).to_equal(0)
    expect(acc.char_quality.value).to_equal(0)

    hass.states.async_set(entity_id, STATE_UNKNOWN)
    await hass.async_block_till_done()
    expect(acc.char_density.value).to_equal(0)
    expect(acc.char_quality.value).to_equal(0)

    hass.states.async_set(entity_id, "34")
    await hass.async_block_till_done()
    expect(acc.char_density.value).to_equal(34)
    expect(acc.char_quality.value).to_equal(2)

    hass.states.async_set(entity_id, "200")
    await hass.async_block_till_done()
    expect(acc.char_density.value).to_equal(200)
    expect(acc.char_quality.value).to_equal(5)


@test
async def pm10(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "sensor.air_quality_pm10"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = PM10Sensor(hass, hk_driver, "PM10 Sensor", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    expect(acc.aid).to_equal(2)
    expect(acc.category).to_equal(10)
    expect(acc.char_density.value).to_equal(0)
    expect(acc.char_quality.value).to_equal(0)

    hass.states.async_set(entity_id, STATE_UNKNOWN)
    await hass.async_block_till_done()
    expect(acc.char_density.value).to_equal(0)
    expect(acc.char_quality.value).to_equal(0)

    for value, quality in [(54, 1), (154, 2), (254, 3), (354, 4), (400, 5)]:
        hass.states.async_set(entity_id, str(value))
        await hass.async_block_till_done()
        expect(acc.char_density.value).to_equal(value)
        expect(acc.char_quality.value).to_equal(quality)


@test
async def pm25(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "sensor.air_quality_pm25"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = PM25Sensor(hass, hk_driver, "PM25 Sensor", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    expect(acc.aid).to_equal(2)
    expect(acc.category).to_equal(10)
    expect(acc.char_density.value).to_equal(0)
    expect(acc.char_quality.value).to_equal(0)

    hass.states.async_set(entity_id, STATE_UNKNOWN)
    await hass.async_block_till_done()
    expect(acc.char_density.value).to_equal(0)
    expect(acc.char_quality.value).to_equal(0)

    for value, quality in [
        (8, 1),
        (12, 2),
        (23, 2),
        (34, 2),
        (90, 4),
        (200, 5),
        (400, 5),
    ]:
        hass.states.async_set(entity_id, str(value))
        await hass.async_block_till_done()
        expect(acc.char_density.value).to_equal(value)
        expect(acc.char_quality.value).to_equal(quality)


@test
async def no2(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "sensor.air_quality_nitrogen_dioxide"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = NitrogenDioxideSensor(
        hass, hk_driver, "Nitrogen Dioxide Sensor", entity_id, 2, None
    )
    acc.run()
    await hass.async_block_till_done()

    expect(acc.aid).to_equal(2)
    expect(acc.category).to_equal(10)
    expect(acc.char_density.value).to_equal(0)
    expect(acc.char_quality.value).to_equal(0)

    hass.states.async_set(entity_id, STATE_UNKNOWN)
    await hass.async_block_till_done()
    expect(acc.char_density.value).to_equal(0)
    expect(acc.char_quality.value).to_equal(0)

    for value, quality in [(30, 1), (60, 2), (80, 3), (90, 4), (100, 5)]:
        hass.states.async_set(entity_id, str(value))
        await hass.async_block_till_done()
        expect(acc.char_density.value).to_equal(value)
        expect(acc.char_quality.value).to_equal(quality)


@test
async def voc(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "sensor.air_quality_volatile_organic_compounds"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = VolatileOrganicCompoundsSensor(
        hass, hk_driver, "Volatile Organic Compounds Sensor", entity_id, 2, None
    )
    acc.run()
    await hass.async_block_till_done()

    expect(acc.aid).to_equal(2)
    expect(acc.category).to_equal(10)
    expect(acc.char_density.value).to_equal(0)
    expect(acc.char_quality.value).to_equal(0)

    hass.states.async_set(entity_id, STATE_UNKNOWN)
    await hass.async_block_till_done()
    expect(acc.char_density.value).to_equal(0)
    expect(acc.char_quality.value).to_equal(0)

    for value, quality in [(250, 1), (500, 2), (1000, 3), (3000, 4), (5000, 5)]:
        hass.states.async_set(entity_id, str(value))
        await hass.async_block_till_done()
        expect(acc.char_density.value).to_equal(value)
        expect(acc.char_quality.value).to_equal(quality)


@test
async def co(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "sensor.co"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = CarbonMonoxideSensor(hass, hk_driver, "CO", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    expect(acc.aid).to_equal(2)
    expect(acc.category).to_equal(10)
    expect(acc.char_level.value).to_equal(0)
    expect(acc.char_peak.value).to_equal(0)
    expect(acc.char_detected.value).to_equal(0)

    hass.states.async_set(entity_id, STATE_UNKNOWN)
    await hass.async_block_till_done()
    expect(acc.char_level.value).to_equal(0)
    expect(acc.char_peak.value).to_equal(0)
    expect(acc.char_detected.value).to_equal(0)

    value = 32
    expect(value > THRESHOLD_CO).to_be(True)
    hass.states.async_set(entity_id, str(value))
    await hass.async_block_till_done()
    expect(acc.char_level.value).to_equal(32)
    expect(acc.char_peak.value).to_equal(32)
    expect(acc.char_detected.value).to_equal(1)

    value = 10
    expect(value < THRESHOLD_CO).to_be(True)
    hass.states.async_set(entity_id, str(value))
    await hass.async_block_till_done()
    expect(acc.char_level.value).to_equal(10)
    expect(acc.char_peak.value).to_equal(32)
    expect(acc.char_detected.value).to_equal(0)


@test
async def co_with_configured_threshold(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if co threshold of accessory can be configured."""
    entity_id = "sensor.co"

    co_threshold = 10
    expect(co_threshold < THRESHOLD_CO).to_be(True)

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = CarbonMonoxideSensor(
        hass, hk_driver, "CO", entity_id, 2, {CONF_THRESHOLD_CO: co_threshold}
    )
    acc.run()
    await hass.async_block_till_done()

    value = 15
    expect(value > co_threshold).to_be(True)
    hass.states.async_set(entity_id, str(value))
    await hass.async_block_till_done()
    expect(acc.char_detected.value).to_equal(1)

    value = 5
    expect(value < co_threshold).to_be(True)
    hass.states.async_set(entity_id, str(value))
    await hass.async_block_till_done()
    expect(acc.char_detected.value).to_equal(0)


@test
async def co2(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "sensor.co2"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = CarbonDioxideSensor(hass, hk_driver, "CO2", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    expect(acc.aid).to_equal(2)
    expect(acc.category).to_equal(10)
    expect(acc.char_level.value).to_equal(0)
    expect(acc.char_peak.value).to_equal(0)
    expect(acc.char_detected.value).to_equal(0)

    hass.states.async_set(entity_id, STATE_UNKNOWN)
    await hass.async_block_till_done()
    expect(acc.char_level.value).to_equal(0)
    expect(acc.char_peak.value).to_equal(0)
    expect(acc.char_detected.value).to_equal(0)

    value = 1100
    expect(value > THRESHOLD_CO2).to_be(True)
    hass.states.async_set(entity_id, str(value))
    await hass.async_block_till_done()
    expect(acc.char_level.value).to_equal(1100)
    expect(acc.char_peak.value).to_equal(1100)
    expect(acc.char_detected.value).to_equal(1)

    value = 800
    expect(value < THRESHOLD_CO2).to_be(True)
    hass.states.async_set(entity_id, str(value))
    await hass.async_block_till_done()
    expect(acc.char_level.value).to_equal(800)
    expect(acc.char_peak.value).to_equal(1100)
    expect(acc.char_detected.value).to_equal(0)


@test
async def co2_with_configured_threshold(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if co2 threshold of accessory can be configured."""
    entity_id = "sensor.co2"

    co2_threshold = 500
    expect(co2_threshold < THRESHOLD_CO2).to_be(True)

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = CarbonDioxideSensor(
        hass, hk_driver, "CO2", entity_id, 2, {CONF_THRESHOLD_CO2: co2_threshold}
    )
    acc.run()
    await hass.async_block_till_done()

    value = 800
    expect(value > co2_threshold).to_be(True)
    hass.states.async_set(entity_id, str(value))
    await hass.async_block_till_done()
    expect(acc.char_detected.value).to_equal(1)

    value = 400
    expect(value < co2_threshold).to_be(True)
    hass.states.async_set(entity_id, str(value))
    await hass.async_block_till_done()
    expect(acc.char_detected.value).to_equal(0)


@test
async def light(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "sensor.light"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = LightSensor(hass, hk_driver, "Light", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    expect(acc.aid).to_equal(2)
    expect(acc.category).to_equal(10)

    expect(acc.char_light.value).to_equal(0.0001)

    hass.states.async_set(entity_id, STATE_UNKNOWN)
    await hass.async_block_till_done()
    expect(acc.char_light.value).to_equal(0.0001)

    hass.states.async_set(entity_id, "300")
    await hass.async_block_till_done()
    expect(acc.char_light.value).to_equal(300)

    hass.states.async_set(entity_id, "0")
    await hass.async_block_till_done()
    expect(acc.char_light.value).to_equal(0.0001)


@test
async def binary(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "binary_sensor.opening"

    hass.states.async_set(entity_id, STATE_UNKNOWN, {ATTR_DEVICE_CLASS: "opening"})
    await hass.async_block_till_done()

    acc = BinarySensor(hass, hk_driver, "Window Opening", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    expect(acc.aid).to_equal(2)
    expect(acc.category).to_equal(10)

    expect(acc.char_detected.value).to_equal(0)

    hass.states.async_set(entity_id, STATE_ON, {ATTR_DEVICE_CLASS: "opening"})
    await hass.async_block_till_done()
    expect(acc.char_detected.value).to_equal(1)

    hass.states.async_set(entity_id, STATE_OFF, {ATTR_DEVICE_CLASS: "opening"})
    await hass.async_block_till_done()
    expect(acc.char_detected.value).to_equal(0)

    hass.states.async_set(entity_id, STATE_UNKNOWN, {ATTR_DEVICE_CLASS: "opening"})
    await hass.async_block_till_done()
    expect(acc.char_detected.value).to_equal(0)

    hass.states.async_set(
        entity_id, STATE_UNAVAILABLE, {ATTR_DEVICE_CLASS: "opening"}
    )
    await hass.async_block_till_done()
    expect(acc.char_detected.value).to_equal(0)

    hass.states.async_remove(entity_id)
    await hass.async_block_till_done()
    expect(acc.char_detected.value).to_equal(0)


@test
async def motion_uses_bool(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "binary_sensor.motion"

    hass.states.async_set(
        entity_id, STATE_UNKNOWN, {ATTR_DEVICE_CLASS: BinarySensorDeviceClass.MOTION}
    )
    await hass.async_block_till_done()

    acc = BinarySensor(hass, hk_driver, "Motion Sensor", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    expect(acc.aid).to_equal(2)
    expect(acc.category).to_equal(10)

    expect(acc.char_detected.value).to_be(False)

    hass.states.async_set(
        entity_id, STATE_ON, {ATTR_DEVICE_CLASS: BinarySensorDeviceClass.MOTION}
    )
    await hass.async_block_till_done()
    expect(acc.char_detected.value).to_be(True)

    hass.states.async_set(
        entity_id, STATE_OFF, {ATTR_DEVICE_CLASS: BinarySensorDeviceClass.MOTION}
    )
    await hass.async_block_till_done()
    expect(acc.char_detected.value).to_be(False)

    hass.states.async_set(
        entity_id, STATE_UNKNOWN, {ATTR_DEVICE_CLASS: BinarySensorDeviceClass.MOTION}
    )
    await hass.async_block_till_done()
    expect(acc.char_detected.value).to_be(False)

    hass.states.async_set(
        entity_id,
        STATE_UNAVAILABLE,
        {ATTR_DEVICE_CLASS: BinarySensorDeviceClass.MOTION},
    )
    await hass.async_block_till_done()
    expect(acc.char_detected.value).to_be(False)

    hass.states.async_remove(entity_id)
    await hass.async_block_till_done()
    expect(acc.char_detected.value).to_be(False)


@test
async def binary_device_classes(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if services and characteristics are assigned correctly."""
    entity_id = "binary_sensor.demo"
    aid = 1

    for device_class, (service, char, _) in BINARY_SENSOR_SERVICE_MAP.items():
        hass.states.async_set(entity_id, STATE_OFF, {ATTR_DEVICE_CLASS: device_class})
        await hass.async_block_till_done()

        aid += 1
        acc = BinarySensor(hass, hk_driver, "Binary Sensor", entity_id, aid, None)
        expect(acc.get_service(service).display_name).to_equal(service)
        expect(acc.char_detected.display_name).to_equal(char)


@test
async def sensor_restore(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test setting up an entity from state in the event registry."""
    hass.set_state(CoreState.not_running)

    entity_registry.async_get_or_create(
        "sensor",
        "generic",
        "1234",
        suggested_object_id="temperature",
        original_device_class="temperature",
    )
    entity_registry.async_get_or_create(
        "sensor",
        "generic",
        "12345",
        suggested_object_id="humidity",
        original_device_class="humidity",
        unit_of_measurement=PERCENTAGE,
    )
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START, {})
    await hass.async_block_till_done()

    acc = get_accessory(hass, hk_driver, hass.states.get("sensor.temperature"), 2, {})
    expect(acc.category).to_equal(10)

    acc = get_accessory(hass, hk_driver, hass.states.get("sensor.humidity"), 3, {})
    expect(acc.category).to_equal(10)


@test
async def bad_name(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test an entity with a bad name."""
    entity_id = "sensor.humidity"

    hass.states.async_set(entity_id, "20")
    await hass.async_block_till_done()
    acc = HumiditySensor(hass, hk_driver, "[[Humid]]", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    expect(acc.aid).to_equal(2)
    expect(acc.category).to_equal(10)

    expect(acc.char_humidity.value).to_equal(20)
    expect(acc.display_name).to_equal("Humid")


@test
async def empty_name(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test an entity with an empty name."""
    entity_id = "sensor.humidity"

    hass.states.async_set(entity_id, "20")
    await hass.async_block_till_done()
    acc = HumiditySensor(hass, hk_driver, None, entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    expect(acc.aid).to_equal(2)
    expect(acc.category).to_equal(10)

    expect(acc.char_humidity.value).to_equal(20)
    expect(acc.display_name).to_equal("None")
