"""Test the Number significant change platform."""

from typing import Any

from tryke import expect, test

from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.number.significant_change import (
    async_check_significant_change,
)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    UnitOfTemperature,
)

AQI_ATTRS = {ATTR_DEVICE_CLASS: NumberDeviceClass.AQI}
BATTERY_ATTRS = {ATTR_DEVICE_CLASS: NumberDeviceClass.BATTERY}
CO_ATTRS = {ATTR_DEVICE_CLASS: NumberDeviceClass.CO}
CO2_ATTRS = {ATTR_DEVICE_CLASS: NumberDeviceClass.CO2}
HUMIDITY_ATTRS = {ATTR_DEVICE_CLASS: NumberDeviceClass.HUMIDITY}
MOISTURE_ATTRS = {ATTR_DEVICE_CLASS: NumberDeviceClass.MOISTURE}
PM1_ATTRS = {ATTR_DEVICE_CLASS: NumberDeviceClass.PM1}
PM10_ATTRS = {ATTR_DEVICE_CLASS: NumberDeviceClass.PM10}
PM25_ATTRS = {ATTR_DEVICE_CLASS: NumberDeviceClass.PM25}
POWER_FACTOR_ATTRS = {ATTR_DEVICE_CLASS: NumberDeviceClass.POWER_FACTOR}
POWER_FACTOR_ATTRS_PERCENTAGE = {
    ATTR_DEVICE_CLASS: NumberDeviceClass.POWER_FACTOR,
    ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE,
}
TEMP_CELSIUS_ATTRS = {
    ATTR_DEVICE_CLASS: NumberDeviceClass.TEMPERATURE,
    ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
}
TEMP_FREEDOM_ATTRS = {
    ATTR_DEVICE_CLASS: NumberDeviceClass.TEMPERATURE,
    ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT,
}
TEMP_DELTA_CELSIUS_ATTRS = {
    ATTR_DEVICE_CLASS: NumberDeviceClass.TEMPERATURE_DELTA,
    ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
}
TEMP_DELTA_FAHRENHEIT_ATTRS = {
    ATTR_DEVICE_CLASS: NumberDeviceClass.TEMPERATURE_DELTA,
    ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT,
}
VOC_ATTRS = {ATTR_DEVICE_CLASS: NumberDeviceClass.VOLATILE_ORGANIC_COMPOUNDS}

@test.cases(
    test.case("no_attrs", old_state="0", new_state="0.9", attrs={}, result=None),
    test.case("aqi_0_to_1", old_state="0", new_state="1", attrs=AQI_ATTRS, result=True),
    test.case("aqi_1_to_0", old_state="1", new_state="0", attrs=AQI_ATTRS, result=True),
    test.case("aqi_0.1_to_0.5", old_state="0.1", new_state="0.5", attrs=AQI_ATTRS, result=False),
    test.case("aqi_0.5_to_0.1", old_state="0.5", new_state="0.1", attrs=AQI_ATTRS, result=False),
    test.case("aqi_99_to_100", old_state="99", new_state="100", attrs=AQI_ATTRS, result=False),
    test.case("aqi_100_to_99", old_state="100", new_state="99", attrs=AQI_ATTRS, result=False),
    test.case("aqi_101_to_99", old_state="101", new_state="99", attrs=AQI_ATTRS, result=False),
    test.case("aqi_99_to_101", old_state="99", new_state="101", attrs=AQI_ATTRS, result=True),
    test.case("bat_100_to_100", old_state="100", new_state="100", attrs=BATTERY_ATTRS, result=False),
    test.case("bat_100_to_99", old_state="100", new_state="99", attrs=BATTERY_ATTRS, result=True),
    test.case("co_0_to_1", old_state="0", new_state="1", attrs=CO_ATTRS, result=True),
    test.case("co_0.1_to_0.5", old_state="0.1", new_state="0.5", attrs=CO_ATTRS, result=False),
    test.case("co2_0_to_1", old_state="0", new_state="1", attrs=CO2_ATTRS, result=True),
    test.case("co2_0.1_to_0.5", old_state="0.1", new_state="0.5", attrs=CO2_ATTRS, result=False),
    test.case("hum_100_to_100", old_state="100", new_state="100", attrs=HUMIDITY_ATTRS, result=False),
    test.case("hum_100_to_99", old_state="100", new_state="99", attrs=HUMIDITY_ATTRS, result=True),
    test.case("moist_100_to_100", old_state="100", new_state="100", attrs=MOISTURE_ATTRS, result=False),
    test.case("moist_100_to_99", old_state="100", new_state="99", attrs=MOISTURE_ATTRS, result=True),
    test.case("pm1_0_to_1", old_state="0", new_state="1", attrs=PM1_ATTRS, result=True),
    test.case("pm1_0.1_to_0.5", old_state="0.1", new_state="0.5", attrs=PM1_ATTRS, result=False),
    test.case("pm10_0_to_1", old_state="0", new_state="1", attrs=PM10_ATTRS, result=True),
    test.case("pm10_0.1_to_0.5", old_state="0.1", new_state="0.5", attrs=PM10_ATTRS, result=False),
    test.case("pm25_0_to_1", old_state="0", new_state="1", attrs=PM25_ATTRS, result=True),
    test.case("pm25_0.1_to_0.5", old_state="0.1", new_state="0.5", attrs=PM25_ATTRS, result=False),
    test.case("pf_0.1_to_0.2", old_state="0.1", new_state="0.2", attrs=POWER_FACTOR_ATTRS, result=True),
    test.case("pf_0.1_to_0.19", old_state="0.1", new_state="0.19", attrs=POWER_FACTOR_ATTRS, result=False),
    test.case("pf_pct_1_to_2", old_state="1", new_state="2", attrs=POWER_FACTOR_ATTRS_PERCENTAGE, result=True),
    test.case("pf_pct_1_to_1.9", old_state="1", new_state="1.9", attrs=POWER_FACTOR_ATTRS_PERCENTAGE, result=False),
    test.case("temp_c_12_to_12", old_state="12", new_state="12", attrs=TEMP_CELSIUS_ATTRS, result=False),
    test.case("temp_c_12_to_13", old_state="12", new_state="13", attrs=TEMP_CELSIUS_ATTRS, result=True),
    test.case("temp_c_12.1_to_12.2", old_state="12.1", new_state="12.2", attrs=TEMP_CELSIUS_ATTRS, result=False),
    test.case("temp_f_70_to_71", old_state="70", new_state="71", attrs=TEMP_FREEDOM_ATTRS, result=True),
    test.case("temp_f_70_to_70.5", old_state="70", new_state="70.5", attrs=TEMP_FREEDOM_ATTRS, result=False),
    test.case("temp_f_fail_to_70", old_state="fail", new_state="70", attrs=TEMP_FREEDOM_ATTRS, result=True),
    test.case("temp_f_70_to_fail", old_state="70", new_state="fail", attrs=TEMP_FREEDOM_ATTRS, result=False),
    test.case("temp_dc_1_to_1", old_state="1", new_state="1", attrs=TEMP_DELTA_CELSIUS_ATTRS, result=False),
    test.case("temp_dc_12_to_13", old_state="12", new_state="13", attrs=TEMP_DELTA_CELSIUS_ATTRS, result=True),
    test.case("temp_dc_12.1_to_12.2", old_state="12.1", new_state="12.2", attrs=TEMP_DELTA_CELSIUS_ATTRS, result=False),
    test.case("temp_df_10_to_11", old_state="10", new_state="11", attrs=TEMP_DELTA_FAHRENHEIT_ATTRS, result=True),
    test.case("temp_df_10_to_10.5", old_state="10", new_state="10.5", attrs=TEMP_DELTA_FAHRENHEIT_ATTRS, result=False),
    test.case("temp_df_fail_to_0", old_state="fail", new_state="0", attrs=TEMP_DELTA_FAHRENHEIT_ATTRS, result=True),
    test.case("temp_df_10_to_fail", old_state="10", new_state="fail", attrs=TEMP_DELTA_FAHRENHEIT_ATTRS, result=False),
    test.case("voc_0_to_1", old_state="0", new_state="1", attrs=VOC_ATTRS, result=True),
    test.case("voc_0.1_to_0.5", old_state="0.1", new_state="0.5", attrs=VOC_ATTRS, result=False),
)
async def significant_change_temperature(
    old_state: str,
    new_state: str,
    attrs: dict[str, Any],
    result: bool | None,
) -> None:
    """Detect temperature significant changes."""
    expect(
        async_check_significant_change(None, old_state, attrs, new_state, attrs)
        is result
    ).to_be(True)
