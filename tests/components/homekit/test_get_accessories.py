"""Package to test the get_accessory method (tryke port)."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.climate import ClimateEntityFeature
from homeassistant.components.cover import CoverEntityFeature
from homeassistant.components.homekit import TYPE_AIR_PURIFIER
from homeassistant.components.homekit.accessories import TYPES, get_accessory
from homeassistant.components.homekit.const import (
    ATTR_INTEGRATION,
    CONF_FEATURE_LIST,
    FEATURE_ON_OFF,
    TYPE_FAN,
    TYPE_FAUCET,
    TYPE_OUTLET,
    TYPE_SHOWER,
    TYPE_SPRINKLER,
    TYPE_SWITCH,
    TYPE_VALVE,
)
from homeassistant.components.homekit.type_sensors import (
    AirQualitySensor,
    CarbonDioxideSensor,
    PM10Sensor,
    PM25Sensor,
    TemperatureSensor,
)
from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntityFeature,
)
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.components.vacuum import VacuumEntityFeature
from homeassistant.const import (
    ATTR_CODE,
    ATTR_DEVICE_CLASS,
    ATTR_SUPPORTED_FEATURES,
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_NAME,
    CONF_TYPE,
    LIGHT_LUX,
    PERCENTAGE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import State

from tests.hass_fixtures import LogCapture, caplog as caplog_fixture


@fixture
def _trigger_executor() -> None:
    """Module-local anchor fixture (see PATTERNS.md)."""
    return None


def _get_identified_type(
    entity_id: str, attrs: dict[str, Any], config: dict[str, Any] | None = None
):
    """Return the accessory type name selected by get_accessory."""

    def passthrough(type_: type):
        return lambda *args, **kwargs: type_

    with patch.dict(
        TYPES, {type_name: passthrough(v) for type_name, v in TYPES.items()}
    ):
        entity_state = State(entity_id, "irrelevant", attrs)
        return get_accessory(None, None, entity_state, 2, config or {})


@test
def not_supported(
    _t: None = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test if none is returned if entity isn't supported."""
    expect(get_accessory(None, None, State("demo.demo", "on"), 2, {})).to_be(None)

    expect(get_accessory(None, None, State("light.demo", "on"), None, None)).to_be(
        None
    )
    expect(caplog.records[0].levelname).to_equal("WARNING")
    expect("invalid aid" in caplog.records[0].msg).to_be(True)


@test
def not_supported_sensor(
    _t: None = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test if none is returned if entity isn't supported."""
    expect(get_accessory(None, None, State("sensor.xyz", "on"), 2, {})).to_be(None)
    expect("Unsupported sensor type (device_class=None)" in caplog.text).to_be(True)


@test
def not_supported_media_player_test() -> None:
    """Test if mode isn't supported and if no supported modes."""
    config = {CONF_FEATURE_LIST: {FEATURE_ON_OFF: None}}
    entity_state = State("media_player.demo", "on")
    expect(get_accessory(None, None, entity_state, 2, config)).to_be(None)

    entity_state = State("media_player.demo", "on")
    expect(get_accessory(None, None, entity_state, 2, {})).to_be(None)


@test.cases(
    test.case("customize_name", config={CONF_NAME: "Customize Name"}, name="Customize Name"),
)
def customize_options(*, config: dict[str, Any], name: str) -> None:
    """Test with customized options."""
    mock_type = Mock()
    conf = config.copy()
    conf[ATTR_INTEGRATION] = "platform_name"
    with patch.dict(TYPES, {"Light": mock_type}):
        entity_state = State("light.demo", "on")
        get_accessory(None, None, entity_state, 2, conf)
    mock_type.assert_called_with(None, None, name, "light.demo", 2, conf)


@test.cases(
    test.case("fan", type_name="Fan", entity_id="fan.test", state="on", attrs={}, config={}),
    test.case("light", type_name="Light", entity_id="light.test", state="on", attrs={}, config={}),
    test.case(
        "lock",
        type_name="Lock",
        entity_id="lock.test",
        state="locked",
        attrs={},
        config={ATTR_CODE: "1234"},
    ),
    test.case(
        "security_system",
        type_name="SecuritySystem",
        entity_id="alarm_control_panel.test",
        state="armed_away",
        attrs={},
        config={ATTR_CODE: "1234"},
    ),
    test.case(
        "thermostat",
        type_name="Thermostat",
        entity_id="climate.test",
        state="auto",
        attrs={},
        config={},
    ),
    test.case(
        "thermostat_target_range",
        type_name="Thermostat",
        entity_id="climate.test",
        state="auto",
        attrs={ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE_RANGE},
        config={},
    ),
    test.case(
        "humidifier_dehumidifier",
        type_name="HumidifierDehumidifier",
        entity_id="humidifier.test",
        state="auto",
        attrs={},
        config={},
    ),
    test.case(
        "water_heater",
        type_name="WaterHeater",
        entity_id="water_heater.test",
        state="auto",
        attrs={},
        config={},
    ),
)
def types(
    *,
    type_name: str,
    entity_id: str,
    state: str,
    attrs: dict[str, Any],
    config: dict[str, Any],
) -> None:
    """Test if types are associated correctly."""
    mock_type = Mock()
    with patch.dict(TYPES, {type_name: mock_type}):
        entity_state = State(entity_id, state, attrs)
        get_accessory(None, None, entity_state, 2, config)
    expect(mock_type.called).to_be(True)

    if config:
        expect(mock_type.call_args[0][-1]).to_equal(config)


@test.cases(
    test.case(
        "garage_door_opener",
        type_name="GarageDoorOpener",
        entity_id="cover.garage_door",
        state="open",
        attrs={
            ATTR_DEVICE_CLASS: "garage",
            ATTR_SUPPORTED_FEATURES: CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE,
        },
    ),
    test.case(
        "window",
        type_name="Window",
        entity_id="cover.set_position",
        state="open",
        attrs={
            ATTR_DEVICE_CLASS: "window",
            ATTR_SUPPORTED_FEATURES: CoverEntityFeature.SET_POSITION,
        },
    ),
    test.case(
        "window_covering_position",
        type_name="WindowCovering",
        entity_id="cover.set_position",
        state="open",
        attrs={ATTR_SUPPORTED_FEATURES: CoverEntityFeature.SET_POSITION},
    ),
    test.case(
        "window_covering_tilt",
        type_name="WindowCovering",
        entity_id="cover.tilt",
        state="open",
        attrs={ATTR_SUPPORTED_FEATURES: CoverEntityFeature.SET_TILT_POSITION},
    ),
    test.case(
        "window_covering_basic_open_close",
        type_name="WindowCoveringBasic",
        entity_id="cover.open_window",
        state="open",
        attrs={
            ATTR_SUPPORTED_FEATURES: (
                CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE
            )
        },
    ),
    test.case(
        "window_covering_basic_with_tilt",
        type_name="WindowCoveringBasic",
        entity_id="cover.open_window",
        state="open",
        attrs={
            ATTR_SUPPORTED_FEATURES: (
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.SET_TILT_POSITION
            )
        },
    ),
    test.case(
        "door",
        type_name="Door",
        entity_id="cover.door",
        state="open",
        attrs={
            ATTR_DEVICE_CLASS: "door",
            ATTR_SUPPORTED_FEATURES: CoverEntityFeature.SET_POSITION,
        },
    ),
)
def type_covers(
    *,
    type_name: str,
    entity_id: str,
    state: str,
    attrs: dict[str, Any],
) -> None:
    """Test if cover types are associated correctly."""
    mock_type = Mock()
    with patch.dict(TYPES, {type_name: mock_type}):
        entity_state = State(entity_id, state, attrs)
        get_accessory(None, None, entity_state, 2, {})
    expect(mock_type.called).to_be(True)


@test.cases(
    test.case(
        "media_player",
        type_name="MediaPlayer",
        entity_id="media_player.test",
        state="on",
        attrs={
            ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
        },
        config={CONF_FEATURE_LIST: {FEATURE_ON_OFF: None}},
    ),
    test.case(
        "tv",
        type_name="TelevisionMediaPlayer",
        entity_id="media_player.tv",
        state="on",
        attrs={ATTR_DEVICE_CLASS: MediaPlayerDeviceClass.TV},
        config={},
    ),
    test.case(
        "receiver",
        type_name="ReceiverMediaPlayer",
        entity_id="media_player.receiver",
        state="on",
        attrs={ATTR_DEVICE_CLASS: MediaPlayerDeviceClass.RECEIVER},
        config={},
    ),
)
def type_media_player(
    *,
    type_name: str,
    entity_id: str,
    state: str,
    attrs: dict[str, Any],
    config: dict[str, Any],
) -> None:
    """Test if media_player types are associated correctly."""
    mock_type = Mock()
    with patch.dict(TYPES, {type_name: mock_type}):
        entity_state = State(entity_id, state, attrs)
        get_accessory(None, None, entity_state, 2, config)
    expect(mock_type.called).to_be(True)

    if config:
        expect(mock_type.call_args[0][-1]).to_equal(config)


@test.cases(
    test.case("binary_opening", type_name="BinarySensor", entity_id="binary_sensor.opening", state="on", attrs={ATTR_DEVICE_CLASS: "opening"}),
    test.case("binary_device_tracker", type_name="BinarySensor", entity_id="device_tracker.someone", state="not_home", attrs={}),
    test.case("binary_person", type_name="BinarySensor", entity_id="person.someone", state="home", attrs={}),
    test.case("pm10_id", type_name="PM10Sensor", entity_id="sensor.air_quality_pm10", state="30", attrs={}),
    test.case("pm10_dc", type_name="PM10Sensor", entity_id="sensor.air_quality", state="30", attrs={ATTR_DEVICE_CLASS: "pm10"}),
    test.case("pm25_id", type_name="PM25Sensor", entity_id="sensor.air_quality_pm25", state="40", attrs={}),
    test.case("pm25_dc", type_name="PM25Sensor", entity_id="sensor.air_quality", state="40", attrs={ATTR_DEVICE_CLASS: "pm25"}),
    test.case(
        "no2",
        type_name="NitrogenDioxideSensor",
        entity_id="sensor.air_quality_nitrogen_dioxide",
        state="50",
        attrs={ATTR_DEVICE_CLASS: SensorDeviceClass.NITROGEN_DIOXIDE},
    ),
    test.case(
        "voc",
        type_name="VolatileOrganicCompoundsSensor",
        entity_id="sensor.air_quality_volatile_organic_compounds",
        state="55",
        attrs={ATTR_DEVICE_CLASS: SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS},
    ),
    test.case(
        "co",
        type_name="CarbonMonoxideSensor",
        entity_id="sensor.co",
        state="2",
        attrs={ATTR_DEVICE_CLASS: SensorDeviceClass.CO},
    ),
    test.case("co2_id", type_name="CarbonDioxideSensor", entity_id="sensor.airmeter_co2", state="500", attrs={}),
    test.case(
        "co2_dc",
        type_name="CarbonDioxideSensor",
        entity_id="sensor.co2",
        state="500",
        attrs={ATTR_DEVICE_CLASS: SensorDeviceClass.CO2},
    ),
    test.case(
        "humidity",
        type_name="HumiditySensor",
        entity_id="sensor.humidity",
        state="20",
        attrs={ATTR_DEVICE_CLASS: "humidity", ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE},
    ),
    test.case(
        "light_dc",
        type_name="LightSensor",
        entity_id="sensor.light",
        state="900",
        attrs={ATTR_DEVICE_CLASS: "illuminance"},
    ),
    test.case(
        "light_uom",
        type_name="LightSensor",
        entity_id="sensor.light",
        state="900",
        attrs={ATTR_UNIT_OF_MEASUREMENT: LIGHT_LUX},
    ),
    test.case(
        "temp_dc",
        type_name="TemperatureSensor",
        entity_id="sensor.temperature",
        state="23",
        attrs={ATTR_DEVICE_CLASS: "temperature"},
    ),
    test.case(
        "temp_celsius",
        type_name="TemperatureSensor",
        entity_id="sensor.temperature",
        state="23",
        attrs={ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    ),
    test.case(
        "temp_fahrenheit",
        type_name="TemperatureSensor",
        entity_id="sensor.temperature",
        state="74",
        attrs={ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT},
    ),
)
def type_sensors(
    *, type_name: str, entity_id: str, state: str, attrs: dict[str, Any]
) -> None:
    """Test if sensor types are associated correctly."""
    mock_type = Mock()
    with patch.dict(TYPES, {type_name: mock_type}):
        entity_state = State(entity_id, state, attrs)
        get_accessory(None, None, entity_state, 2, {})
    expect(mock_type.called).to_be(True)


@test.cases(
    test.case("outlet_type", type_name="Outlet", entity_id="switch.test", state="on", attrs={}, config={CONF_TYPE: TYPE_OUTLET}),
    test.case(
        "outlet_dc",
        type_name="Outlet",
        entity_id="switch.test",
        state="on",
        attrs={ATTR_DEVICE_CLASS: SwitchDeviceClass.OUTLET},
        config={},
    ),
    test.case("automation", type_name="Switch", entity_id="automation.test", state="on", attrs={}, config={}),
    test.case("button", type_name="Switch", entity_id="button.test", state=STATE_UNKNOWN, attrs={}, config={}),
    test.case("input_boolean", type_name="Switch", entity_id="input_boolean.test", state="on", attrs={}, config={}),
    test.case("input_button", type_name="Switch", entity_id="input_button.test", state=STATE_UNKNOWN, attrs={}, config={}),
    test.case("remote", type_name="Switch", entity_id="remote.test", state="on", attrs={}, config={}),
    test.case("scene", type_name="Switch", entity_id="scene.test", state="on", attrs={}, config={}),
    test.case("script", type_name="Switch", entity_id="script.test", state="on", attrs={}, config={}),
    test.case("input_select", type_name="SelectSwitch", entity_id="input_select.test", state="option1", attrs={}, config={}),
    test.case("select", type_name="SelectSwitch", entity_id="select.test", state="option1", attrs={}, config={}),
    test.case("switch", type_name="Switch", entity_id="switch.test", state="on", attrs={}, config={}),
    test.case("switch_type", type_name="Switch", entity_id="switch.test", state="on", attrs={}, config={CONF_TYPE: TYPE_SWITCH}),
    test.case("valve_faucet", type_name="ValveSwitch", entity_id="switch.test", state="on", attrs={}, config={CONF_TYPE: TYPE_FAUCET}),
    test.case("valve_valve", type_name="ValveSwitch", entity_id="switch.test", state="on", attrs={}, config={CONF_TYPE: TYPE_VALVE}),
    test.case("valve_shower", type_name="ValveSwitch", entity_id="switch.test", state="on", attrs={}, config={CONF_TYPE: TYPE_SHOWER}),
    test.case("valve_sprinkler", type_name="ValveSwitch", entity_id="switch.test", state="on", attrs={}, config={CONF_TYPE: TYPE_SPRINKLER}),
)
def type_switches(
    *,
    type_name: str,
    entity_id: str,
    state: str,
    attrs: dict[str, Any],
    config: dict[str, Any],
) -> None:
    """Test if switch types are associated correctly."""
    mock_type = Mock()
    with patch.dict(TYPES, {type_name: mock_type}):
        entity_state = State(entity_id, state, attrs)
        get_accessory(None, None, entity_state, 2, config)
    expect(mock_type.called).to_be(True)


@test.cases(
    test.case("fan_basic", type_name="Fan", entity_id="fan.test", state="on", attrs={}, config={}),
    test.case("fan_type", type_name="Fan", entity_id="fan.test", state="on", attrs={}, config={CONF_TYPE: TYPE_FAN}),
    test.case("air_purifier", type_name="AirPurifier", entity_id="fan.test", state="on", attrs={}, config={CONF_TYPE: TYPE_AIR_PURIFIER}),
)
def type_fans(
    *,
    type_name: str,
    entity_id: str,
    state: str,
    attrs: dict[str, Any],
    config: dict[str, Any],
) -> None:
    """Test if fan types are associated correctly."""
    mock_type = Mock()
    with patch.dict(TYPES, {type_name: mock_type}):
        entity_state = State(entity_id, state, attrs)
        get_accessory(None, None, entity_state, 2, config)
    expect(mock_type.called).to_be(True)


@test.cases(
    test.case("valve", type_name="Valve", entity_id="valve.test", state="on", attrs={}),
)
def type_valve(
    *, type_name: str, entity_id: str, state: str, attrs: dict[str, Any]
) -> None:
    """Test if valve types are associated correctly."""
    mock_type = Mock()
    with patch.dict(TYPES, {type_name: mock_type}):
        entity_state = State(entity_id, state, attrs)
        get_accessory(None, None, entity_state, 2, {})
    expect(mock_type.called).to_be(True)


@test.cases(
    test.case(
        "dock_vacuum",
        type_name="Vacuum",
        entity_id="vacuum.dock_vacuum",
        state="docked",
        attrs={
            ATTR_SUPPORTED_FEATURES: VacuumEntityFeature.START
            | VacuumEntityFeature.RETURN_HOME
        },
    ),
    test.case(
        "basic_vacuum",
        type_name="Vacuum",
        entity_id="vacuum.basic_vacuum",
        state="off",
        attrs={},
    ),
)
def type_vacuum(
    *, type_name: str, entity_id: str, state: str, attrs: dict[str, Any]
) -> None:
    """Test if vacuum types are associated correctly."""
    mock_type = Mock()
    with patch.dict(TYPES, {type_name: mock_type}):
        entity_state = State(entity_id, state, attrs)
        get_accessory(None, None, entity_state, 2, {})
    expect(mock_type.called).to_be(True)


@test.cases(
    test.case("camera_basic", type_name="Camera", entity_id="camera.basic", state="on", attrs={}),
)
def type_camera(
    *, type_name: str, entity_id: str, state: str, attrs: dict[str, Any]
) -> None:
    """Test if camera types are associated correctly."""
    mock_type = Mock()
    with patch.dict(TYPES, {type_name: mock_type}):
        entity_state = State(entity_id, state, attrs)
        get_accessory(None, None, entity_state, 2, {})
    expect(mock_type.called).to_be(True)


@test.cases(
    test.case(
        "pm10",
        expected_type=PM10Sensor,
        entity_id="sensor.air_quality_pm25",
        attrs={ATTR_DEVICE_CLASS: SensorDeviceClass.PM10},
    ),
    test.case(
        "pm25",
        expected_type=PM25Sensor,
        entity_id="sensor.air_quality_pm10",
        attrs={ATTR_DEVICE_CLASS: SensorDeviceClass.PM25},
    ),
    test.case(
        "air_quality",
        expected_type=AirQualitySensor,
        entity_id="sensor.co2_sensor",
        attrs={ATTR_DEVICE_CLASS: SensorDeviceClass.GAS},
    ),
    test.case(
        "co2",
        expected_type=CarbonDioxideSensor,
        entity_id="sensor.air_quality_gas",
        attrs={ATTR_DEVICE_CLASS: SensorDeviceClass.CO2},
    ),
    test.case(
        "temperature",
        expected_type=TemperatureSensor,
        entity_id="sensor.random_sensor",
        attrs={ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE},
    ),
)
def explicit_device_class_takes_precedence(
    *, expected_type: type, entity_id: str, attrs: dict[str, Any]
) -> None:
    """Test that explicit device_class takes precedence over entity_id hints."""
    identified_type = _get_identified_type(entity_id, attrs=attrs)
    expect(identified_type is expected_type).to_be(True)


@test.cases(
    test.case("pm10", expected_type=PM10Sensor, entity_id="sensor.air_quality_pm10", attrs={}),
    test.case("pm25", expected_type=PM25Sensor, entity_id="sensor.air_quality_pm25", attrs={}),
    test.case("air_quality", expected_type=AirQualitySensor, entity_id="sensor.air_quality_gas", attrs={}),
    test.case("co2", expected_type=CarbonDioxideSensor, entity_id="sensor.airmeter_co2", attrs={}),
)
def entity_id_fallback_when_no_device_class(
    *, expected_type: type, entity_id: str, attrs: dict[str, Any]
) -> None:
    """Test that entity_id is used as fallback when device_class is not set."""
    identified_type = _get_identified_type(entity_id, attrs=attrs)
    expect(identified_type is expected_type).to_be(True)
