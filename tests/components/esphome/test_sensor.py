"""Test ESPHome sensors."""

import logging
import math

from aioesphomeapi import (
    APIClient,
    EntityCategory as ESPHomeEntityCategory,
    LastResetType,
    SensorInfo,
    SensorState,
    SensorStateClass as ESPHomeSensorStateClass,
    TextSensorInfo,
    TextSensorState,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.sensor import (
    ATTR_STATE_CLASS,
    SensorDeviceClass,
    SensorStateClass,
    async_rounded_state,
)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ICON,
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    STATE_UNKNOWN,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import MockESPHomeDeviceType, mock_client, mock_esphome_device

from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor cross-module fixtures so tryke resolves before the test body."""
    return hass


@test
async def generic_numeric_sensor(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test a generic sensor entity."""
    logging.getLogger("homeassistant.components.esphome").setLevel(logging.DEBUG)
    entity_info = [
        SensorInfo(
            object_id="mysensor",
            key=1,
            name="my sensor",
        )
    ]
    states = [SensorState(key=1, state=50)]
    user_service = []
    mock_device = await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("sensor.test_my_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("50")

    mock_device.set_state(SensorState(key=1, state=60))
    await hass.async_block_till_done()
    state = hass.states.get("sensor.test_my_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("60")

    mock_device.set_state(SensorState(key=1, state=60))
    await hass.async_block_till_done()
    state = hass.states.get("sensor.test_my_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("60")

    mock_device.set_state(SensorState(key=1, state=70))
    await hass.async_block_till_done()
    state = hass.states.get("sensor.test_my_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("70")

    mock_device.set_state(SensorState(key=1, state=object()))
    await hass.async_block_till_done()
    state = hass.states.get("sensor.test_my_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("70")


@test
async def generic_numeric_sensor_with_entity_category_and_icon(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test a generic sensor entity."""
    entity_info = [
        SensorInfo(
            object_id="mysensor",
            key=1,
            name="my sensor",
            entity_category=ESPHomeEntityCategory.DIAGNOSTIC,
            icon="mdi:leaf",
        )
    ]
    states = [SensorState(key=1, state=50)]
    user_service = []
    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("sensor.test_my_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("50")
    expect(state.attributes[ATTR_ICON]).to_equal("mdi:leaf")
    entry = entity_registry.async_get("sensor.test_my_sensor")
    expect(entry is not None).to_be(True)
    expect(entry.unique_id).to_equal("11:22:33:44:55:AA-sensor-mysensor")
    expect(entry.entity_category is EntityCategory.DIAGNOSTIC).to_be(True)


@test
async def generic_numeric_sensor_state_class_measurement(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test a generic sensor entity."""
    entity_info = [
        SensorInfo(
            object_id="mysensor",
            key=1,
            name="my sensor",
            state_class=ESPHomeSensorStateClass.MEASUREMENT,
            device_class="power",
            unit_of_measurement="W",
        )
    ]
    states = [SensorState(key=1, state=50)]
    user_service = []
    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("sensor.test_my_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("50")
    expect(state.attributes[ATTR_STATE_CLASS]).to_equal(SensorStateClass.MEASUREMENT)
    expect(state.attributes[ATTR_DEVICE_CLASS]).to_equal(SensorDeviceClass.POWER)
    expect(state.attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal(UnitOfPower.WATT)
    entry = entity_registry.async_get("sensor.test_my_sensor")
    expect(entry is not None).to_be(True)
    expect(entry.unique_id).to_equal("11:22:33:44:55:AA-sensor-mysensor")
    expect(entry.entity_category is None).to_be(True)


@test
async def generic_numeric_sensor_state_class_measurement_angle(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test a generic sensor entity."""
    entity_info = [
        SensorInfo(
            object_id="mysensor",
            key=1,
            name="my sensor",
            state_class=ESPHomeSensorStateClass.MEASUREMENT_ANGLE,
            unit_of_measurement="°",
        )
    ]
    states = [SensorState(key=1, state=50)]
    user_service = []
    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("sensor.test_my_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("50")
    expect(state.attributes[ATTR_STATE_CLASS]).to_equal(
        SensorStateClass.MEASUREMENT_ANGLE
    )
    expect(state.attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("°")
    entry = entity_registry.async_get("sensor.test_my_sensor")
    expect(entry is not None).to_be(True)
    expect(entry.unique_id).to_equal("11:22:33:44:55:AA-sensor-mysensor")
    expect(entry.entity_category is None).to_be(True)


@test
async def generic_numeric_sensor_device_class_timestamp(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test a sensor entity that uses timestamp (epoch)."""
    entity_info = [
        SensorInfo(
            object_id="mysensor",
            key=1,
            name="my sensor",
            device_class="timestamp",
        )
    ]
    states = [SensorState(key=1, state=1687459432.466624)]
    user_service = []
    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("sensor.test_my_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("2023-06-22T18:43:52+00:00")


@test
async def generic_numeric_sensor_legacy_last_reset_convert(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test a state class of measurement with last reset type of auto is converted to total increasing."""
    entity_info = [
        SensorInfo(
            object_id="mysensor",
            key=1,
            name="my sensor",
            legacy_last_reset_type=LastResetType.AUTO,
            state_class=ESPHomeSensorStateClass.MEASUREMENT,
        )
    ]
    states = [SensorState(key=1, state=50)]
    user_service = []
    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("sensor.test_my_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("50")
    expect(state.attributes[ATTR_STATE_CLASS]).to_equal(
        SensorStateClass.TOTAL_INCREASING
    )


@test
async def generic_numeric_sensor_no_state(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test a generic numeric sensor that has no state."""
    entity_info = [
        SensorInfo(
            object_id="mysensor",
            key=1,
            name="my sensor",
        )
    ]
    states = []
    user_service = []
    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("sensor.test_my_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)


@test
async def generic_numeric_sensor_nan_state(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test a generic numeric sensor that has nan state."""
    entity_info = [
        SensorInfo(
            object_id="mysensor",
            key=1,
            name="my sensor",
        )
    ]
    states = [SensorState(key=1, state=math.nan, missing_state=False)]
    user_service = []
    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("sensor.test_my_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)


@test
async def generic_numeric_sensor_missing_state(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test a generic numeric sensor that is missing state."""
    entity_info = [
        SensorInfo(
            object_id="mysensor",
            key=1,
            name="my sensor",
        )
    ]
    states = [SensorState(key=1, state=True, missing_state=True)]
    user_service = []
    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("sensor.test_my_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)


@test
async def generic_text_sensor(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test a generic text sensor entity."""
    entity_info = [
        TextSensorInfo(
            object_id="mysensor",
            key=1,
            name="my sensor",
        )
    ]
    states = [TextSensorState(key=1, state="i am a teapot")]
    user_service = []
    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("sensor.test_my_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("i am a teapot")


@test
async def generic_text_sensor_missing_state(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test a generic text sensor that is missing state."""
    entity_info = [
        TextSensorInfo(
            object_id="mysensor",
            key=1,
            name="my sensor",
        )
    ]
    states = [TextSensorState(key=1, state=True, missing_state=True)]
    user_service = []
    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("sensor.test_my_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)


@test
async def generic_text_sensor_device_class_timestamp(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test a sensor entity that uses timestamp (datetime)."""
    entity_info = [
        TextSensorInfo(
            object_id="mysensor",
            key=1,
            name="my sensor",
            device_class=SensorDeviceClass.TIMESTAMP,
        )
    ]
    states = [TextSensorState(key=1, state="2023-06-22T18:43:52+00:00")]
    user_service = []
    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("sensor.test_my_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("2023-06-22T18:43:52+00:00")
    expect(state.attributes[ATTR_DEVICE_CLASS]).to_equal(SensorDeviceClass.TIMESTAMP)


@test
async def generic_text_sensor_device_class_date(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test a sensor entity that uses date (datetime)."""
    entity_info = [
        TextSensorInfo(
            object_id="mysensor",
            key=1,
            name="my sensor",
            device_class=SensorDeviceClass.DATE,
        )
    ]
    states = [TextSensorState(key=1, state="2023-06-22T18:43:52+00:00")]
    user_service = []
    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("sensor.test_my_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("2023-06-22")
    expect(state.attributes[ATTR_DEVICE_CLASS]).to_equal(SensorDeviceClass.DATE)


@test
async def generic_numeric_sensor_empty_string_uom(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test a generic numeric sensor that has an empty string as the uom."""
    entity_info = [
        SensorInfo(
            object_id="mysensor",
            key=1,
            name="my sensor",
            unit_of_measurement="",
        )
    ]
    states = [SensorState(key=1, state=123, missing_state=False)]
    user_service = []
    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("sensor.test_my_sensor")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("123")
    expect(ATTR_UNIT_OF_MEASUREMENT not in state.attributes).to_be(True)


@test.cases(
    test.case(
        "temp_23",
        device_class=SensorDeviceClass.TEMPERATURE,
        unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_value=23.456,
        expected_precision=1,
    ),
    test.case(
        "temp_0_1",
        device_class=SensorDeviceClass.TEMPERATURE,
        unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_value=0.1,
        expected_precision=1,
    ),
    test.case(
        "temp_neg",
        device_class=SensorDeviceClass.TEMPERATURE,
        unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_value=-25.789,
        expected_precision=1,
    ),
    test.case(
        "power_1234",
        device_class=SensorDeviceClass.POWER,
        unit_of_measurement=UnitOfPower.WATT,
        state_value=1234.56,
        expected_precision=0,
    ),
    test.case(
        "power_1_23",
        device_class=SensorDeviceClass.POWER,
        unit_of_measurement=UnitOfPower.WATT,
        state_value=1.23456,
        expected_precision=3,
    ),
    test.case(
        "power_0_123",
        device_class=SensorDeviceClass.POWER,
        unit_of_measurement=UnitOfPower.WATT,
        state_value=0.123,
        expected_precision=3,
    ),
    test.case(
        "energy_1234",
        device_class=SensorDeviceClass.ENERGY,
        unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_value=1234.5,
        expected_precision=0,
    ),
    test.case(
        "energy_12_3",
        device_class=SensorDeviceClass.ENERGY,
        unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_value=12.3456,
        expected_precision=2,
    ),
    test.case(
        "voltage_230",
        device_class=SensorDeviceClass.VOLTAGE,
        unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_value=230.45,
        expected_precision=1,
    ),
    test.case(
        "voltage_3_3",
        device_class=SensorDeviceClass.VOLTAGE,
        unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_value=3.3,
        expected_precision=1,
    ),
    test.case(
        "current_15",
        device_class=SensorDeviceClass.CURRENT,
        unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_value=15.678,
        expected_precision=2,
    ),
    test.case(
        "current_0_015",
        device_class=SensorDeviceClass.CURRENT,
        unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_value=0.015,
        expected_precision=3,
    ),
    test.case(
        "atmos_pressure",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        unit_of_measurement=UnitOfPressure.HPA,
        state_value=1013.25,
        expected_precision=1,
    ),
    test.case(
        "pressure_bar",
        device_class=SensorDeviceClass.PRESSURE,
        unit_of_measurement=UnitOfPressure.BAR,
        state_value=1.01325,
        expected_precision=3,
    ),
    test.case(
        "volume_45",
        device_class=SensorDeviceClass.VOLUME,
        unit_of_measurement=UnitOfVolume.LITERS,
        state_value=45.67,
        expected_precision=1,
    ),
    test.case(
        "volume_4567",
        device_class=SensorDeviceClass.VOLUME,
        unit_of_measurement=UnitOfVolume.LITERS,
        state_value=4567.0,
        expected_precision=0,
    ),
    test.case(
        "humidity_87",
        device_class=SensorDeviceClass.HUMIDITY,
        unit_of_measurement=PERCENTAGE,
        state_value=87.654,
        expected_precision=1,
    ),
    test.case(
        "humidity_45",
        device_class=SensorDeviceClass.HUMIDITY,
        unit_of_measurement=PERCENTAGE,
        state_value=45.2,
        expected_precision=1,
    ),
    test.case(
        "battery_95",
        device_class=SensorDeviceClass.BATTERY,
        unit_of_measurement=PERCENTAGE,
        state_value=95.2,
        expected_precision=1,
    ),
    test.case(
        "battery_100",
        device_class=SensorDeviceClass.BATTERY,
        unit_of_measurement=PERCENTAGE,
        state_value=100.0,
        expected_precision=1,
    ),
)
async def suggested_display_precision_by_device_class(
    device_class: SensorDeviceClass,
    unit_of_measurement: str,
    state_value: float,
    expected_precision: int,
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test suggested display precision for different device classes."""
    entity_info = [
        SensorInfo(
            object_id="mysensor",
            key=1,
            name="my sensor",
            accuracy_decimals=expected_precision,
            device_class=device_class.value,
            unit_of_measurement=unit_of_measurement,
        )
    ]
    states = [SensorState(key=1, state=state_value)]
    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        states=states,
    )

    state = hass.states.get("sensor.test_my_sensor")
    expect(state is not None).to_be(True)
    rounded = float(async_rounded_state(hass, "sensor.test_my_sensor", state))
    expected = round(state_value, expected_precision)
    expect(math.isclose(rounded, expected, rel_tol=1e-6, abs_tol=1e-9)).to_be(True)
