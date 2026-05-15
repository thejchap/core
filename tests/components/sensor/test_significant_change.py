"""Test the sensor significant change platform."""

from typing import Any

from tryke import expect, test

from homeassistant.components.sensor import SensorDeviceClass, significant_change
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    UnitOfTemperature,
)

AQI_ATTRS = {
    ATTR_DEVICE_CLASS: SensorDeviceClass.AQI,
}

BATTERY_ATTRS = {
    ATTR_DEVICE_CLASS: SensorDeviceClass.BATTERY,
}

HUMIDITY_ATTRS = {
    ATTR_DEVICE_CLASS: SensorDeviceClass.HUMIDITY,
}

TEMP_CELSIUS_ATTRS = {
    ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
    ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
}

TEMP_FREEDOM_ATTRS = {
    ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
    ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT,
}

TEMP_DELTA_CELSIUS_ATTRS = {
    ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE_DELTA,
    ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
}

TEMP_DELTA_FAHRENHEIT_ATTRS = {
    ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE_DELTA,
    ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT,
}


@test.cases(
    test.case("aqi_0_to_1", old_state="0", new_state="1", attrs=AQI_ATTRS, result=True),
    test.case("aqi_1_to_0", old_state="1", new_state="0", attrs=AQI_ATTRS, result=True),
    test.case(
        "aqi_0.1_to_0.5",
        old_state="0.1",
        new_state="0.5",
        attrs=AQI_ATTRS,
        result=False,
    ),
    test.case(
        "aqi_0.5_to_0.1",
        old_state="0.5",
        new_state="0.1",
        attrs=AQI_ATTRS,
        result=False,
    ),
    test.case(
        "aqi_99_to_100", old_state="99", new_state="100", attrs=AQI_ATTRS, result=False
    ),
    test.case(
        "aqi_100_to_99", old_state="100", new_state="99", attrs=AQI_ATTRS, result=False
    ),
    test.case(
        "aqi_101_to_99", old_state="101", new_state="99", attrs=AQI_ATTRS, result=False
    ),
    test.case(
        "aqi_99_to_101", old_state="99", new_state="101", attrs=AQI_ATTRS, result=True
    ),
    test.case(
        "battery_100_to_100",
        old_state="100",
        new_state="100",
        attrs=BATTERY_ATTRS,
        result=False,
    ),
    test.case(
        "battery_100_to_99",
        old_state="100",
        new_state="99",
        attrs=BATTERY_ATTRS,
        result=True,
    ),
    test.case(
        "humidity_100_to_100",
        old_state="100",
        new_state="100",
        attrs=HUMIDITY_ATTRS,
        result=False,
    ),
    test.case(
        "humidity_100_to_99",
        old_state="100",
        new_state="99",
        attrs=HUMIDITY_ATTRS,
        result=True,
    ),
    test.case(
        "temp_c_12_to_12",
        old_state="12",
        new_state="12",
        attrs=TEMP_CELSIUS_ATTRS,
        result=False,
    ),
    test.case(
        "temp_c_12_to_13",
        old_state="12",
        new_state="13",
        attrs=TEMP_CELSIUS_ATTRS,
        result=True,
    ),
    test.case(
        "temp_c_12.1_to_12.2",
        old_state="12.1",
        new_state="12.2",
        attrs=TEMP_CELSIUS_ATTRS,
        result=False,
    ),
    test.case(
        "temp_f_70_to_71",
        old_state="70",
        new_state="71",
        attrs=TEMP_FREEDOM_ATTRS,
        result=True,
    ),
    test.case(
        "temp_f_70_to_70.5",
        old_state="70",
        new_state="70.5",
        attrs=TEMP_FREEDOM_ATTRS,
        result=False,
    ),
    test.case(
        "temp_f_fail_to_70",
        old_state="fail",
        new_state="70",
        attrs=TEMP_FREEDOM_ATTRS,
        result=True,
    ),
    test.case(
        "temp_f_70_to_fail",
        old_state="70",
        new_state="fail",
        attrs=TEMP_FREEDOM_ATTRS,
        result=False,
    ),
    test.case(
        "temp_delta_c_12_to_12",
        old_state="12",
        new_state="12",
        attrs=TEMP_DELTA_CELSIUS_ATTRS,
        result=False,
    ),
    test.case(
        "temp_delta_c_12_to_13",
        old_state="12",
        new_state="13",
        attrs=TEMP_DELTA_CELSIUS_ATTRS,
        result=True,
    ),
    test.case(
        "temp_delta_c_12.1_to_12.2",
        old_state="12.1",
        new_state="12.2",
        attrs=TEMP_DELTA_CELSIUS_ATTRS,
        result=False,
    ),
    test.case(
        "temp_delta_f_7_to_8",
        old_state="7",
        new_state="8",
        attrs=TEMP_DELTA_FAHRENHEIT_ATTRS,
        result=True,
    ),
    test.case(
        "temp_delta_f_7_to_7.5",
        old_state="7",
        new_state="7.5",
        attrs=TEMP_DELTA_FAHRENHEIT_ATTRS,
        result=False,
    ),
)
async def significant_change_temperature(
    old_state: str,
    new_state: str,
    attrs: dict[str, Any],
    result: bool,
) -> None:
    """Detect temperature significant changes."""
    expect(
        significant_change.async_check_significant_change(
            None, old_state, attrs, new_state, attrs
        )
        is result
    ).to_be(True)
