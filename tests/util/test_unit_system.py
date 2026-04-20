"""Test the unit system helper."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.components.sensor import DEVICE_CLASS_UNITS, SensorDeviceClass
from homeassistant.const import (
    ACCUMULATED_PRECIPITATION,
    AREA,
    LENGTH,
    MASS,
    PRESSURE,
    TEMPERATURE,
    VOLUME,
    WIND_SPEED,
    UnitOfArea,
    UnitOfLength,
    UnitOfMass,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolume,
    UnitOfVolumetricFlux,
)
from homeassistant.core import HomeAssistant
from homeassistant.core_config import async_process_ha_core_config
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util.unit_system import (  # pylint: disable=hass-deprecated-import
    _CONF_UNIT_SYSTEM_IMPERIAL,
    _CONF_UNIT_SYSTEM_METRIC,
    _CONF_UNIT_SYSTEM_US_CUSTOMARY,
    IMPERIAL_SYSTEM,
    METRIC_SYSTEM,
    US_CUSTOMARY_SYSTEM,
    UnitSystem,
    get_unit_system,
)

from tests.hass_fixtures import hass

SYSTEM_NAME = "TEST"
INVALID_UNIT = "INVALID"


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture so imported `hass` resolves via Depends()."""
    return 0


@test
def invalid_units() -> None:
    """Test errors are raised when invalid units are passed in."""
    expect(
        lambda: UnitSystem(
            SYSTEM_NAME,
            accumulated_precipitation=UnitOfPrecipitationDepth.MILLIMETERS,
            area=UnitOfArea.SQUARE_METERS,
            conversions={},
            length=UnitOfLength.METERS,
            mass=UnitOfMass.GRAMS,
            pressure=UnitOfPressure.PA,
            temperature=INVALID_UNIT,
            volume=UnitOfVolume.LITERS,
            wind_speed=UnitOfSpeed.METERS_PER_SECOND,
        )
    ).to_raise(ValueError)

    expect(
        lambda: UnitSystem(
            SYSTEM_NAME,
            accumulated_precipitation=UnitOfPrecipitationDepth.MILLIMETERS,
            area=UnitOfArea.SQUARE_METERS,
            conversions={},
            length=INVALID_UNIT,
            mass=UnitOfMass.GRAMS,
            pressure=UnitOfPressure.PA,
            temperature=UnitOfTemperature.CELSIUS,
            volume=UnitOfVolume.LITERS,
            wind_speed=UnitOfSpeed.METERS_PER_SECOND,
        )
    ).to_raise(ValueError)

    expect(
        lambda: UnitSystem(
            SYSTEM_NAME,
            accumulated_precipitation=UnitOfPrecipitationDepth.MILLIMETERS,
            area=UnitOfArea.SQUARE_METERS,
            conversions={},
            length=UnitOfLength.METERS,
            mass=UnitOfMass.GRAMS,
            pressure=UnitOfPressure.PA,
            temperature=UnitOfTemperature.CELSIUS,
            volume=UnitOfVolume.LITERS,
            wind_speed=INVALID_UNIT,
        )
    ).to_raise(ValueError)

    expect(
        lambda: UnitSystem(
            SYSTEM_NAME,
            accumulated_precipitation=UnitOfPrecipitationDepth.MILLIMETERS,
            area=UnitOfArea.SQUARE_METERS,
            conversions={},
            length=UnitOfLength.METERS,
            mass=UnitOfMass.GRAMS,
            pressure=UnitOfPressure.PA,
            temperature=UnitOfTemperature.CELSIUS,
            volume=INVALID_UNIT,
            wind_speed=UnitOfSpeed.METERS_PER_SECOND,
        )
    ).to_raise(ValueError)

    expect(
        lambda: UnitSystem(
            SYSTEM_NAME,
            accumulated_precipitation=UnitOfPrecipitationDepth.MILLIMETERS,
            area=UnitOfArea.SQUARE_METERS,
            conversions={},
            length=UnitOfLength.METERS,
            mass=INVALID_UNIT,
            pressure=UnitOfPressure.PA,
            temperature=UnitOfTemperature.CELSIUS,
            volume=UnitOfVolume.LITERS,
            wind_speed=UnitOfSpeed.METERS_PER_SECOND,
        )
    ).to_raise(ValueError)

    expect(
        lambda: UnitSystem(
            SYSTEM_NAME,
            accumulated_precipitation=UnitOfPrecipitationDepth.MILLIMETERS,
            area=UnitOfArea.SQUARE_METERS,
            conversions={},
            length=UnitOfLength.METERS,
            mass=UnitOfMass.GRAMS,
            pressure=INVALID_UNIT,
            temperature=UnitOfTemperature.CELSIUS,
            volume=UnitOfVolume.LITERS,
            wind_speed=UnitOfSpeed.METERS_PER_SECOND,
        )
    ).to_raise(ValueError)

    expect(
        lambda: UnitSystem(
            SYSTEM_NAME,
            accumulated_precipitation=INVALID_UNIT,
            area=UnitOfArea.SQUARE_METERS,
            conversions={},
            length=UnitOfLength.METERS,
            mass=UnitOfMass.GRAMS,
            pressure=UnitOfPressure.PA,
            temperature=UnitOfTemperature.CELSIUS,
            volume=UnitOfVolume.LITERS,
            wind_speed=UnitOfSpeed.METERS_PER_SECOND,
        )
    ).to_raise(ValueError)

    expect(
        lambda: UnitSystem(
            SYSTEM_NAME,
            accumulated_precipitation=UnitOfPrecipitationDepth.MILLIMETERS,
            area=INVALID_UNIT,
            conversions={},
            length=UnitOfLength.METERS,
            mass=UnitOfMass.GRAMS,
            pressure=UnitOfPressure.PA,
            temperature=UnitOfTemperature.CELSIUS,
            volume=UnitOfVolume.LITERS,
            wind_speed=UnitOfSpeed.METERS_PER_SECOND,
        )
    ).to_raise(ValueError)


@test
def invalid_value() -> None:
    """Test no conversion happens if value is non-numeric."""
    expect(lambda: METRIC_SYSTEM.length("25a", UnitOfLength.KILOMETERS)).to_raise(
        TypeError
    )
    expect(
        lambda: METRIC_SYSTEM.temperature("50K", UnitOfTemperature.CELSIUS)
    ).to_raise(TypeError)
    expect(
        lambda: METRIC_SYSTEM.wind_speed("50km/h", UnitOfSpeed.METERS_PER_SECOND)
    ).to_raise(TypeError)
    expect(lambda: METRIC_SYSTEM.volume("50L", UnitOfVolume.LITERS)).to_raise(TypeError)
    expect(lambda: METRIC_SYSTEM.pressure("50Pa", UnitOfPressure.PA)).to_raise(
        TypeError
    )
    expect(
        lambda: METRIC_SYSTEM.accumulated_precipitation(
            "50mm", UnitOfLength.MILLIMETERS
        )
    ).to_raise(TypeError)
    expect(lambda: METRIC_SYSTEM.area("2m²", UnitOfArea.SQUARE_METERS)).to_raise(
        TypeError
    )


@test
def as_dict() -> None:
    """Test the as_dict method returns the expected dictionary."""
    expected = {
        LENGTH: UnitOfLength.KILOMETERS,
        WIND_SPEED: UnitOfSpeed.METERS_PER_SECOND,
        TEMPERATURE: UnitOfTemperature.CELSIUS,
        VOLUME: UnitOfVolume.LITERS,
        MASS: UnitOfMass.GRAMS,
        PRESSURE: UnitOfPressure.PA,
        ACCUMULATED_PRECIPITATION: UnitOfLength.MILLIMETERS,
        AREA: UnitOfArea.SQUARE_METERS,
    }

    expect(METRIC_SYSTEM.as_dict()).to_equal(expected)


@test
def temperature_same_unit() -> None:
    """Test no conversion happens if to unit is same as from unit."""
    expect(METRIC_SYSTEM.temperature(5, METRIC_SYSTEM.temperature_unit)).to_equal(5)


@test
def temperature_unknown_unit() -> None:
    """Test no conversion happens if unknown unit."""
    expect(lambda: METRIC_SYSTEM.temperature(5, "abc")).to_raise(
        HomeAssistantError, match="is not a recognized .* unit"
    )


@test
def temperature_to_metric() -> None:
    """Test temperature conversion to metric system."""
    expect(METRIC_SYSTEM.temperature(25, METRIC_SYSTEM.temperature_unit)).to_equal(25)
    expect(
        round(METRIC_SYSTEM.temperature(80, IMPERIAL_SYSTEM.temperature_unit), 1)
    ).to_equal(26.7)


@test
def temperature_to_imperial() -> None:
    """Test temperature conversion to imperial system."""
    expect(IMPERIAL_SYSTEM.temperature(77, IMPERIAL_SYSTEM.temperature_unit)).to_equal(
        77
    )
    expect(IMPERIAL_SYSTEM.temperature(25, METRIC_SYSTEM.temperature_unit)).to_equal(77)


@test
def length_unknown_unit() -> None:
    """Test length conversion with unknown from unit."""
    expect(lambda: METRIC_SYSTEM.length(5, "fr")).to_raise(
        HomeAssistantError, match="is not a recognized .* unit"
    )


@test
def length_to_metric() -> None:
    """Test length conversion to metric system."""
    expect(METRIC_SYSTEM.length(100, METRIC_SYSTEM.length_unit)).to_equal(100)
    expect(
        abs(METRIC_SYSTEM.length(5, IMPERIAL_SYSTEM.length_unit) - 8.04672) < 1e-6
    ).to_be(True)


@test
def length_to_imperial() -> None:
    """Test length conversion to imperial system."""
    expect(IMPERIAL_SYSTEM.length(100, IMPERIAL_SYSTEM.length_unit)).to_equal(100)
    expect(
        abs(IMPERIAL_SYSTEM.length(5, METRIC_SYSTEM.length_unit) - 3.106855) < 1e-6
    ).to_be(True)


@test
def wind_speed_unknown_unit() -> None:
    """Test wind_speed conversion with unknown from unit."""
    expect(lambda: METRIC_SYSTEM.length(5, "turtles")).to_raise(
        HomeAssistantError, match="is not a recognized .* unit"
    )


@test
def wind_speed_to_metric() -> None:
    """Test length conversion to metric system."""
    expect(METRIC_SYSTEM.wind_speed(100, METRIC_SYSTEM.wind_speed_unit)).to_equal(100)
    # 1 m/s is about 2.237 mph.
    expect(
        abs(METRIC_SYSTEM.wind_speed(2237, IMPERIAL_SYSTEM.wind_speed_unit) - 1000)
        < 0.1
    ).to_be(True)


@test
def wind_speed_to_imperial() -> None:
    """Test wind_speed conversion to imperial system."""
    expect(IMPERIAL_SYSTEM.wind_speed(100, IMPERIAL_SYSTEM.wind_speed_unit)).to_equal(
        100
    )
    expect(
        abs(IMPERIAL_SYSTEM.wind_speed(1000, METRIC_SYSTEM.wind_speed_unit) - 2237)
        < 0.1
    ).to_be(True)


@test
def pressure_same_unit() -> None:
    """Test no conversion happens if to unit is same as from unit."""
    expect(METRIC_SYSTEM.pressure(5, METRIC_SYSTEM.pressure_unit)).to_equal(5)


@test
def pressure_unknown_unit() -> None:
    """Test no conversion happens if unknown unit."""
    expect(lambda: METRIC_SYSTEM.pressure(5, "K")).to_raise(
        HomeAssistantError, match="is not a recognized .* unit"
    )


@test
def pressure_to_metric() -> None:
    """Test pressure conversion to metric system."""
    expect(METRIC_SYSTEM.pressure(25, METRIC_SYSTEM.pressure_unit)).to_equal(25)
    expect(
        abs(METRIC_SYSTEM.pressure(14.7, IMPERIAL_SYSTEM.pressure_unit) - 101352.932)
        < 1e-1
    ).to_be(True)


@test
def pressure_to_imperial() -> None:
    """Test pressure conversion to imperial system."""
    expect(IMPERIAL_SYSTEM.pressure(77, IMPERIAL_SYSTEM.pressure_unit)).to_equal(77)
    expect(
        abs(IMPERIAL_SYSTEM.pressure(101352.932, METRIC_SYSTEM.pressure_unit) - 14.7)
        < 1e-4
    ).to_be(True)


@test
def accumulated_precipitation_same_unit() -> None:
    """Test no conversion happens if to unit is same as from unit."""
    expect(
        METRIC_SYSTEM.accumulated_precipitation(
            5, METRIC_SYSTEM.accumulated_precipitation_unit
        )
    ).to_equal(5)


@test
def accumulated_precipitation_unknown_unit() -> None:
    """Test no conversion happens if unknown unit."""
    expect(lambda: METRIC_SYSTEM.accumulated_precipitation(5, "K")).to_raise(
        HomeAssistantError, match="is not a recognized .* unit"
    )


@test
def accumulated_precipitation_to_metric() -> None:
    """Test accumulated_precipitation conversion to metric system."""
    expect(
        METRIC_SYSTEM.accumulated_precipitation(
            25, METRIC_SYSTEM.accumulated_precipitation_unit
        )
    ).to_equal(25)
    expect(
        abs(
            METRIC_SYSTEM.accumulated_precipitation(
                10, IMPERIAL_SYSTEM.accumulated_precipitation_unit
            )
            - 254
        )
        < 1e-4
    ).to_be(True)


@test
def accumulated_precipitation_to_imperial() -> None:
    """Test accumulated_precipitation conversion to imperial system."""
    expect(
        IMPERIAL_SYSTEM.accumulated_precipitation(
            10, IMPERIAL_SYSTEM.accumulated_precipitation_unit
        )
    ).to_equal(10)
    expect(
        abs(
            IMPERIAL_SYSTEM.accumulated_precipitation(
                254, METRIC_SYSTEM.accumulated_precipitation_unit
            )
            - 10
        )
        < 1e-4
    ).to_be(True)


@test
def area_same_unit() -> None:
    """Test no conversion happens if to unit is same as from unit."""
    expect(METRIC_SYSTEM.area(5, METRIC_SYSTEM.area_unit)).to_equal(5)


@test
def area_unknown_unit() -> None:
    """Test no conversion happens if unknown unit."""
    expect(lambda: METRIC_SYSTEM.area(5, "abc")).to_raise(
        HomeAssistantError, match="is not a recognized .* unit"
    )


@test
def area_to_metric() -> None:
    """Test area conversion to metric system."""
    expect(METRIC_SYSTEM.area(25, METRIC_SYSTEM.area_unit)).to_equal(25)
    expect(round(METRIC_SYSTEM.area(10, IMPERIAL_SYSTEM.area_unit), 1)).to_equal(0.9)


@test
def area_to_imperial() -> None:
    """Test area conversion to imperial system."""
    expect(IMPERIAL_SYSTEM.area(77, IMPERIAL_SYSTEM.area_unit)).to_equal(77)
    expect(IMPERIAL_SYSTEM.area(25, METRIC_SYSTEM.area_unit)).to_equal(
        269.09776041774313
    )


@test
def properties() -> None:
    """Test the unit properties are returned as expected."""
    expect(METRIC_SYSTEM.length_unit).to_equal(UnitOfLength.KILOMETERS)
    expect(METRIC_SYSTEM.wind_speed_unit).to_equal(UnitOfSpeed.METERS_PER_SECOND)
    expect(METRIC_SYSTEM.temperature_unit).to_equal(UnitOfTemperature.CELSIUS)
    expect(METRIC_SYSTEM.mass_unit).to_equal(UnitOfMass.GRAMS)
    expect(METRIC_SYSTEM.volume_unit).to_equal(UnitOfVolume.LITERS)
    expect(METRIC_SYSTEM.pressure_unit).to_equal(UnitOfPressure.PA)
    expect(METRIC_SYSTEM.accumulated_precipitation_unit).to_equal(
        UnitOfLength.MILLIMETERS
    )
    expect(METRIC_SYSTEM.area_unit).to_equal(UnitOfArea.SQUARE_METERS)


@test.cases(
    test.case("metric", key=_CONF_UNIT_SYSTEM_METRIC, expected_system=METRIC_SYSTEM),
    test.case(
        "us-customary",
        key=_CONF_UNIT_SYSTEM_US_CUSTOMARY,
        expected_system=US_CUSTOMARY_SYSTEM,
    ),
)
def get_unit_system_(key: str, expected_system: UnitSystem) -> None:
    """Test get_unit_system."""
    expect(get_unit_system(key)).to_be(expected_system)


@test.cases(
    test.case("none", key=None),
    test.case("empty", key=""),
    test.case("invalid-custom", key="invalid_custom"),
    test.case("imperial", key=_CONF_UNIT_SYSTEM_IMPERIAL),
)
def get_unit_system_invalid(key: str) -> None:
    """Test get_unit_system with an invalid key."""
    expect(lambda: get_unit_system(key)).to_raise(
        ValueError, match=f"`{key}` is not a valid unit system key"
    )


@test.cases(
    # Test area conversion.
    test.case(
        "area-square-feet",
        device_class=SensorDeviceClass.AREA,
        original_unit=UnitOfArea.SQUARE_FEET,
        state_unit=UnitOfArea.SQUARE_METERS,
    ),
    test.case(
        "area-square-inches",
        device_class=SensorDeviceClass.AREA,
        original_unit=UnitOfArea.SQUARE_INCHES,
        state_unit=UnitOfArea.SQUARE_CENTIMETERS,
    ),
    test.case(
        "area-square-miles",
        device_class=SensorDeviceClass.AREA,
        original_unit=UnitOfArea.SQUARE_MILES,
        state_unit=UnitOfArea.SQUARE_KILOMETERS,
    ),
    test.case(
        "area-square-yards",
        device_class=SensorDeviceClass.AREA,
        original_unit=UnitOfArea.SQUARE_YARDS,
        state_unit=UnitOfArea.SQUARE_METERS,
    ),
    test.case(
        "area-acres",
        device_class=SensorDeviceClass.AREA,
        original_unit=UnitOfArea.ACRES,
        state_unit=UnitOfArea.HECTARES,
    ),
    test.case(
        "area-square-kilometers-none",
        device_class=SensorDeviceClass.AREA,
        original_unit=UnitOfArea.SQUARE_KILOMETERS,
        state_unit=None,
    ),
    test.case(
        "area-very-long-none",
        device_class=SensorDeviceClass.AREA,
        original_unit="very_long",
        state_unit=None,
    ),
    # Test atmospheric pressure.
    test.case(
        "atm-psi",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        original_unit=UnitOfPressure.PSI,
        state_unit=UnitOfPressure.HPA,
    ),
    test.case(
        "atm-bar",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        original_unit=UnitOfPressure.BAR,
        state_unit=UnitOfPressure.HPA,
    ),
    test.case(
        "atm-inhg",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        original_unit=UnitOfPressure.INHG,
        state_unit=UnitOfPressure.HPA,
    ),
    test.case(
        "atm-hpa-none",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        original_unit=UnitOfPressure.HPA,
        state_unit=None,
    ),
    test.case(
        "atm-very-much-none",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        original_unit="very_much",
        state_unit=None,
    ),
    # Test distance conversion.
    test.case(
        "distance-feet",
        device_class=SensorDeviceClass.DISTANCE,
        original_unit=UnitOfLength.FEET,
        state_unit=UnitOfLength.METERS,
    ),
    test.case(
        "distance-inches",
        device_class=SensorDeviceClass.DISTANCE,
        original_unit=UnitOfLength.INCHES,
        state_unit=UnitOfLength.MILLIMETERS,
    ),
    test.case(
        "distance-miles",
        device_class=SensorDeviceClass.DISTANCE,
        original_unit=UnitOfLength.MILES,
        state_unit=UnitOfLength.KILOMETERS,
    ),
    test.case(
        "distance-yards",
        device_class=SensorDeviceClass.DISTANCE,
        original_unit=UnitOfLength.YARDS,
        state_unit=UnitOfLength.METERS,
    ),
    test.case(
        "distance-kilometers-none",
        device_class=SensorDeviceClass.DISTANCE,
        original_unit=UnitOfLength.KILOMETERS,
        state_unit=None,
    ),
    test.case(
        "distance-very-long-none",
        device_class=SensorDeviceClass.DISTANCE,
        original_unit="very_long",
        state_unit=None,
    ),
    # Test gas meter conversion.
    test.case(
        "gas-centum-cubic-feet",
        device_class=SensorDeviceClass.GAS,
        original_unit=UnitOfVolume.CENTUM_CUBIC_FEET,
        state_unit=UnitOfVolume.CUBIC_METERS,
    ),
    test.case(
        "gas-mille-cubic-feet",
        device_class=SensorDeviceClass.GAS,
        original_unit=UnitOfVolume.MILLE_CUBIC_FEET,
        state_unit=UnitOfVolume.CUBIC_METERS,
    ),
    test.case(
        "gas-cubic-feet",
        device_class=SensorDeviceClass.GAS,
        original_unit=UnitOfVolume.CUBIC_FEET,
        state_unit=UnitOfVolume.CUBIC_METERS,
    ),
    test.case(
        "gas-liters-none",
        device_class=SensorDeviceClass.GAS,
        original_unit=UnitOfVolume.LITERS,
        state_unit=None,
    ),
    test.case(
        "gas-cubic-meters-none",
        device_class=SensorDeviceClass.GAS,
        original_unit=UnitOfVolume.CUBIC_METERS,
        state_unit=None,
    ),
    test.case(
        "gas-very-much-none",
        device_class=SensorDeviceClass.GAS,
        original_unit="very_much",
        state_unit=None,
    ),
    # Test precipitation conversion.
    test.case(
        "precip-inches",
        device_class=SensorDeviceClass.PRECIPITATION,
        original_unit=UnitOfLength.INCHES,
        state_unit=UnitOfLength.MILLIMETERS,
    ),
    test.case(
        "precip-centimeters-none",
        device_class=SensorDeviceClass.PRECIPITATION,
        original_unit=UnitOfLength.CENTIMETERS,
        state_unit=None,
    ),
    test.case(
        "precip-millimeters-none",
        device_class=SensorDeviceClass.PRECIPITATION,
        original_unit=UnitOfLength.MILLIMETERS,
        state_unit=None,
    ),
    test.case(
        "precip-very-much-none",
        device_class=SensorDeviceClass.PRECIPITATION,
        original_unit="very_much",
        state_unit=None,
    ),
    # Test precipitation intensity conversion.
    test.case(
        "precip-intensity-inches-per-day",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        original_unit=UnitOfVolumetricFlux.INCHES_PER_DAY,
        state_unit=UnitOfVolumetricFlux.MILLIMETERS_PER_DAY,
    ),
    test.case(
        "precip-intensity-inches-per-hour",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        original_unit=UnitOfVolumetricFlux.INCHES_PER_HOUR,
        state_unit=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
    ),
    test.case(
        "precip-intensity-mm-per-day-none",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        original_unit=UnitOfVolumetricFlux.MILLIMETERS_PER_DAY,
        state_unit=None,
    ),
    test.case(
        "precip-intensity-mm-per-hour-none",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        original_unit=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        state_unit=None,
    ),
    test.case(
        "precip-intensity-very-heavy-none",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        original_unit="very_heavy",
        state_unit=None,
    ),
    # Test pressure conversion.
    test.case(
        "pressure-psi",
        device_class=SensorDeviceClass.PRESSURE,
        original_unit=UnitOfPressure.PSI,
        state_unit=UnitOfPressure.KPA,
    ),
    test.case(
        "pressure-bar-none",
        device_class=SensorDeviceClass.PRESSURE,
        original_unit=UnitOfPressure.BAR,
        state_unit=None,
    ),
    test.case(
        "pressure-very-much-none",
        device_class=SensorDeviceClass.PRESSURE,
        original_unit="very_much",
        state_unit=None,
    ),
    # Test speed conversion.
    test.case(
        "speed-feet-per-second",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfSpeed.FEET_PER_SECOND,
        state_unit=UnitOfSpeed.KILOMETERS_PER_HOUR,
    ),
    test.case(
        "speed-inches-per-second",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfSpeed.INCHES_PER_SECOND,
        state_unit=UnitOfSpeed.MILLIMETERS_PER_SECOND,
    ),
    test.case(
        "speed-miles-per-hour",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfSpeed.MILES_PER_HOUR,
        state_unit=UnitOfSpeed.KILOMETERS_PER_HOUR,
    ),
    test.case(
        "speed-kilometers-per-hour-none",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_unit=None,
    ),
    test.case(
        "speed-knots-none",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfSpeed.KNOTS,
        state_unit=None,
    ),
    test.case(
        "speed-meters-per-second-none",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfSpeed.METERS_PER_SECOND,
        state_unit=None,
    ),
    test.case(
        "speed-inches-per-day",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfVolumetricFlux.INCHES_PER_DAY,
        state_unit=UnitOfVolumetricFlux.MILLIMETERS_PER_DAY,
    ),
    test.case(
        "speed-inches-per-hour",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfVolumetricFlux.INCHES_PER_HOUR,
        state_unit=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
    ),
    test.case(
        "speed-mm-per-day-none",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfVolumetricFlux.MILLIMETERS_PER_DAY,
        state_unit=None,
    ),
    test.case(
        "speed-mm-per-hour-none",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        state_unit=None,
    ),
    test.case(
        "speed-very-fast-none",
        device_class=SensorDeviceClass.SPEED,
        original_unit="very_fast",
        state_unit=None,
    ),
    # Test volume conversion.
    test.case(
        "volume-centum-cubic-feet",
        device_class=SensorDeviceClass.VOLUME,
        original_unit=UnitOfVolume.CENTUM_CUBIC_FEET,
        state_unit=UnitOfVolume.CUBIC_METERS,
    ),
    test.case(
        "volume-mille-cubic-feet",
        device_class=SensorDeviceClass.VOLUME,
        original_unit=UnitOfVolume.MILLE_CUBIC_FEET,
        state_unit=UnitOfVolume.CUBIC_METERS,
    ),
    test.case(
        "volume-cubic-feet",
        device_class=SensorDeviceClass.VOLUME,
        original_unit=UnitOfVolume.CUBIC_FEET,
        state_unit=UnitOfVolume.CUBIC_METERS,
    ),
    test.case(
        "volume-fluid-ounces",
        device_class=SensorDeviceClass.VOLUME,
        original_unit=UnitOfVolume.FLUID_OUNCES,
        state_unit=UnitOfVolume.MILLILITERS,
    ),
    test.case(
        "volume-gallons",
        device_class=SensorDeviceClass.VOLUME,
        original_unit=UnitOfVolume.GALLONS,
        state_unit=UnitOfVolume.LITERS,
    ),
    test.case(
        "volume-cubic-meters-none",
        device_class=SensorDeviceClass.VOLUME,
        original_unit=UnitOfVolume.CUBIC_METERS,
        state_unit=None,
    ),
    test.case(
        "volume-liters-none",
        device_class=SensorDeviceClass.VOLUME,
        original_unit=UnitOfVolume.LITERS,
        state_unit=None,
    ),
    test.case(
        "volume-milliliters-none",
        device_class=SensorDeviceClass.VOLUME,
        original_unit=UnitOfVolume.MILLILITERS,
        state_unit=None,
    ),
    test.case(
        "volume-very-much-none",
        device_class=SensorDeviceClass.VOLUME,
        original_unit="very_much",
        state_unit=None,
    ),
    # Test water meter conversion.
    test.case(
        "water-centum-cubic-feet",
        device_class=SensorDeviceClass.WATER,
        original_unit=UnitOfVolume.CENTUM_CUBIC_FEET,
        state_unit=UnitOfVolume.CUBIC_METERS,
    ),
    test.case(
        "water-mille-cubic-feet",
        device_class=SensorDeviceClass.WATER,
        original_unit=UnitOfVolume.MILLE_CUBIC_FEET,
        state_unit=UnitOfVolume.CUBIC_METERS,
    ),
    test.case(
        "water-cubic-feet",
        device_class=SensorDeviceClass.WATER,
        original_unit=UnitOfVolume.CUBIC_FEET,
        state_unit=UnitOfVolume.CUBIC_METERS,
    ),
    test.case(
        "water-gallons",
        device_class=SensorDeviceClass.WATER,
        original_unit=UnitOfVolume.GALLONS,
        state_unit=UnitOfVolume.LITERS,
    ),
    test.case(
        "water-cubic-meters-none",
        device_class=SensorDeviceClass.WATER,
        original_unit=UnitOfVolume.CUBIC_METERS,
        state_unit=None,
    ),
    test.case(
        "water-liters-none",
        device_class=SensorDeviceClass.WATER,
        original_unit=UnitOfVolume.LITERS,
        state_unit=None,
    ),
    test.case(
        "water-very-much-none",
        device_class=SensorDeviceClass.WATER,
        original_unit="very_much",
        state_unit=None,
    ),
    # Test wind speed conversion.
    test.case(
        "wind-feet-per-second",
        device_class=SensorDeviceClass.WIND_SPEED,
        original_unit=UnitOfSpeed.FEET_PER_SECOND,
        state_unit=UnitOfSpeed.KILOMETERS_PER_HOUR,
    ),
    test.case(
        "wind-miles-per-hour",
        device_class=SensorDeviceClass.WIND_SPEED,
        original_unit=UnitOfSpeed.MILES_PER_HOUR,
        state_unit=UnitOfSpeed.KILOMETERS_PER_HOUR,
    ),
    test.case(
        "wind-kilometers-per-hour-none",
        device_class=SensorDeviceClass.WIND_SPEED,
        original_unit=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_unit=None,
    ),
    test.case(
        "wind-knots-none",
        device_class=SensorDeviceClass.WIND_SPEED,
        original_unit=UnitOfSpeed.KNOTS,
        state_unit=None,
    ),
    test.case(
        "wind-meters-per-second",
        device_class=SensorDeviceClass.WIND_SPEED,
        original_unit=UnitOfSpeed.METERS_PER_SECOND,
        state_unit=UnitOfSpeed.KILOMETERS_PER_HOUR,
    ),
    test.case(
        "wind-very-fast-none",
        device_class=SensorDeviceClass.WIND_SPEED,
        original_unit="very_fast",
        state_unit=None,
    ),
)
def get_metric_converted_unit_(
    device_class: SensorDeviceClass,
    original_unit: str,
    state_unit: str | None,
) -> None:
    """Test unit conversion rules."""
    unit_system = METRIC_SYSTEM
    expect(unit_system.get_converted_unit(device_class, original_unit)).to_equal(
        state_unit
    )


UNCONVERTED_UNITS_METRIC_SYSTEM = {
    SensorDeviceClass.AREA: (
        UnitOfArea.SQUARE_MILLIMETERS,
        UnitOfArea.SQUARE_CENTIMETERS,
        UnitOfArea.SQUARE_METERS,
        UnitOfArea.SQUARE_KILOMETERS,
        UnitOfArea.HECTARES,
    ),
    SensorDeviceClass.ATMOSPHERIC_PRESSURE: (UnitOfPressure.HPA,),
    SensorDeviceClass.DISTANCE: (
        UnitOfLength.CENTIMETERS,
        UnitOfLength.KILOMETERS,
        UnitOfLength.METERS,
        UnitOfLength.MILLIMETERS,
    ),
    SensorDeviceClass.GAS: (
        UnitOfVolume.CUBIC_METERS,
        UnitOfVolume.LITERS,
    ),
    SensorDeviceClass.PRECIPITATION: (
        UnitOfLength.CENTIMETERS,
        UnitOfLength.MILLIMETERS,
    ),
    SensorDeviceClass.PRECIPITATION_INTENSITY: (
        UnitOfVolumetricFlux.MILLIMETERS_PER_DAY,
        UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
    ),
    SensorDeviceClass.PRESSURE: (
        UnitOfPressure.BAR,
        UnitOfPressure.CBAR,
        UnitOfPressure.HPA,
        UnitOfPressure.KPA,
        UnitOfPressure.MBAR,
        UnitOfPressure.MMHG,
        UnitOfPressure.MILLIPASCAL,
        UnitOfPressure.PA,
    ),
    SensorDeviceClass.SPEED: (
        UnitOfSpeed.BEAUFORT,
        UnitOfSpeed.KILOMETERS_PER_HOUR,
        UnitOfSpeed.KNOTS,
        UnitOfSpeed.METERS_PER_MINUTE,
        UnitOfSpeed.METERS_PER_SECOND,
        UnitOfSpeed.MILLIMETERS_PER_SECOND,
        UnitOfVolumetricFlux.MILLIMETERS_PER_DAY,
        UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
    ),
    SensorDeviceClass.VOLUME: (
        UnitOfVolume.CUBIC_METERS,
        UnitOfVolume.LITERS,
        UnitOfVolume.MILLILITERS,
    ),
    SensorDeviceClass.WATER: (
        UnitOfVolume.CUBIC_METERS,
        UnitOfVolume.LITERS,
    ),
}


@test.cases(
    test.case("area", device_class=SensorDeviceClass.AREA),
    test.case(
        "atmospheric-pressure", device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE
    ),
    test.case("distance", device_class=SensorDeviceClass.DISTANCE),
    test.case("gas", device_class=SensorDeviceClass.GAS),
    test.case("precipitation", device_class=SensorDeviceClass.PRECIPITATION),
    test.case(
        "precipitation-intensity",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
    ),
    test.case("pressure", device_class=SensorDeviceClass.PRESSURE),
    test.case("speed", device_class=SensorDeviceClass.SPEED),
    test.case("volume", device_class=SensorDeviceClass.VOLUME),
    test.case("water", device_class=SensorDeviceClass.WATER),
)
def metric_converted_units(device_class: SensorDeviceClass) -> None:
    """Test unit conversion rules are in place for all units."""
    unit_system = METRIC_SYSTEM
    # Make sure excluded_units is not stale.
    for unit in UNCONVERTED_UNITS_METRIC_SYSTEM[device_class]:
        expect(unit in DEVICE_CLASS_UNITS[device_class]).to_be(True)

    for unit in DEVICE_CLASS_UNITS[device_class]:
        if unit in UNCONVERTED_UNITS_METRIC_SYSTEM[device_class]:
            expect((device_class, unit) not in unit_system._conversions).to_be(True)
            continue
        expect((device_class, unit) in unit_system._conversions).to_be(True)


@test.cases(
    # Test area conversion.
    test.case(
        "area-square-millimeters",
        device_class=SensorDeviceClass.AREA,
        original_unit=UnitOfArea.SQUARE_MILLIMETERS,
        state_unit=UnitOfArea.SQUARE_INCHES,
    ),
    test.case(
        "area-square-centimeters",
        device_class=SensorDeviceClass.AREA,
        original_unit=UnitOfArea.SQUARE_CENTIMETERS,
        state_unit=UnitOfArea.SQUARE_INCHES,
    ),
    test.case(
        "area-square-meters",
        device_class=SensorDeviceClass.AREA,
        original_unit=UnitOfArea.SQUARE_METERS,
        state_unit=UnitOfArea.SQUARE_FEET,
    ),
    test.case(
        "area-square-kilometers",
        device_class=SensorDeviceClass.AREA,
        original_unit=UnitOfArea.SQUARE_KILOMETERS,
        state_unit=UnitOfArea.SQUARE_MILES,
    ),
    test.case(
        "area-hectares",
        device_class=SensorDeviceClass.AREA,
        original_unit=UnitOfArea.HECTARES,
        state_unit=UnitOfArea.ACRES,
    ),
    test.case(
        "area-very-area-none",
        device_class=SensorDeviceClass.AREA,
        original_unit="very_area",
        state_unit=None,
    ),
    # Test atmospheric pressure.
    test.case(
        "atm-psi",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        original_unit=UnitOfPressure.PSI,
        state_unit=UnitOfPressure.INHG,
    ),
    test.case(
        "atm-bar",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        original_unit=UnitOfPressure.BAR,
        state_unit=UnitOfPressure.INHG,
    ),
    test.case(
        "atm-hpa",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        original_unit=UnitOfPressure.HPA,
        state_unit=UnitOfPressure.INHG,
    ),
    test.case(
        "atm-inhg-none",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        original_unit=UnitOfPressure.INHG,
        state_unit=None,
    ),
    test.case(
        "atm-very-much-none",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        original_unit="very_much",
        state_unit=None,
    ),
    # Test distance conversion.
    test.case(
        "distance-centimeters",
        device_class=SensorDeviceClass.DISTANCE,
        original_unit=UnitOfLength.CENTIMETERS,
        state_unit=UnitOfLength.INCHES,
    ),
    test.case(
        "distance-kilometers",
        device_class=SensorDeviceClass.DISTANCE,
        original_unit=UnitOfLength.KILOMETERS,
        state_unit=UnitOfLength.MILES,
    ),
    test.case(
        "distance-meters",
        device_class=SensorDeviceClass.DISTANCE,
        original_unit=UnitOfLength.METERS,
        state_unit=UnitOfLength.FEET,
    ),
    test.case(
        "distance-millimeters",
        device_class=SensorDeviceClass.DISTANCE,
        original_unit=UnitOfLength.MILLIMETERS,
        state_unit=UnitOfLength.INCHES,
    ),
    test.case(
        "distance-miles-none",
        device_class=SensorDeviceClass.DISTANCE,
        original_unit=UnitOfLength.MILES,
        state_unit=None,
    ),
    test.case(
        "distance-very-long-none",
        device_class=SensorDeviceClass.DISTANCE,
        original_unit="very_long",
        state_unit=None,
    ),
    # Test gas meter conversion.
    test.case(
        "gas-centum-cubic-feet-none",
        device_class=SensorDeviceClass.GAS,
        original_unit=UnitOfVolume.CENTUM_CUBIC_FEET,
        state_unit=None,
    ),
    test.case(
        "gas-mille-cubic-feet-none",
        device_class=SensorDeviceClass.GAS,
        original_unit=UnitOfVolume.MILLE_CUBIC_FEET,
        state_unit=None,
    ),
    test.case(
        "gas-cubic-meters",
        device_class=SensorDeviceClass.GAS,
        original_unit=UnitOfVolume.CUBIC_METERS,
        state_unit=UnitOfVolume.CUBIC_FEET,
    ),
    test.case(
        "gas-liters",
        device_class=SensorDeviceClass.GAS,
        original_unit=UnitOfVolume.LITERS,
        state_unit=UnitOfVolume.CUBIC_FEET,
    ),
    test.case(
        "gas-cubic-feet-none",
        device_class=SensorDeviceClass.GAS,
        original_unit=UnitOfVolume.CUBIC_FEET,
        state_unit=None,
    ),
    test.case(
        "gas-very-much-none",
        device_class=SensorDeviceClass.GAS,
        original_unit="very_much",
        state_unit=None,
    ),
    # Test precipitation conversion.
    test.case(
        "precip-centimeters",
        device_class=SensorDeviceClass.PRECIPITATION,
        original_unit=UnitOfLength.CENTIMETERS,
        state_unit=UnitOfLength.INCHES,
    ),
    test.case(
        "precip-millimeters",
        device_class=SensorDeviceClass.PRECIPITATION,
        original_unit=UnitOfLength.MILLIMETERS,
        state_unit=UnitOfLength.INCHES,
    ),
    test.case(
        "precip-inches-none",
        device_class=SensorDeviceClass.PRECIPITATION,
        original_unit=UnitOfLength.INCHES,
        state_unit=None,
    ),
    test.case(
        "precip-very-much-none",
        device_class=SensorDeviceClass.PRECIPITATION,
        original_unit="very_much",
        state_unit=None,
    ),
    # Test precipitation intensity conversion.
    test.case(
        "precip-intensity-mm-per-day",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        original_unit=UnitOfVolumetricFlux.MILLIMETERS_PER_DAY,
        state_unit=UnitOfVolumetricFlux.INCHES_PER_DAY,
    ),
    test.case(
        "precip-intensity-mm-per-hour",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        original_unit=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        state_unit=UnitOfVolumetricFlux.INCHES_PER_HOUR,
    ),
    test.case(
        "precip-intensity-inches-per-day-none",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        original_unit=UnitOfVolumetricFlux.INCHES_PER_DAY,
        state_unit=None,
    ),
    test.case(
        "precip-intensity-inches-per-hour-none",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        original_unit=UnitOfVolumetricFlux.INCHES_PER_HOUR,
        state_unit=None,
    ),
    test.case(
        "precip-intensity-very-heavy-none",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        original_unit="very_heavy",
        state_unit=None,
    ),
    # Test pressure conversion.
    test.case(
        "pressure-bar",
        device_class=SensorDeviceClass.PRESSURE,
        original_unit=UnitOfPressure.BAR,
        state_unit=UnitOfPressure.PSI,
    ),
    test.case(
        "pressure-psi-none",
        device_class=SensorDeviceClass.PRESSURE,
        original_unit=UnitOfPressure.PSI,
        state_unit=None,
    ),
    test.case(
        "pressure-very-much-none",
        device_class=SensorDeviceClass.PRESSURE,
        original_unit="very_much",
        state_unit=None,
    ),
    # Test speed conversion.
    test.case(
        "speed-meters-per-second",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfSpeed.METERS_PER_SECOND,
        state_unit=UnitOfSpeed.MILES_PER_HOUR,
    ),
    test.case(
        "speed-kilometers-per-hour",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_unit=UnitOfSpeed.MILES_PER_HOUR,
    ),
    test.case(
        "speed-feet-per-second-none",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfSpeed.FEET_PER_SECOND,
        state_unit=None,
    ),
    test.case(
        "speed-knots-none",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfSpeed.KNOTS,
        state_unit=None,
    ),
    test.case(
        "speed-miles-per-hour-none",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfSpeed.MILES_PER_HOUR,
        state_unit=None,
    ),
    test.case(
        "speed-mm-per-day",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfVolumetricFlux.MILLIMETERS_PER_DAY,
        state_unit=UnitOfVolumetricFlux.INCHES_PER_DAY,
    ),
    test.case(
        "speed-mm-per-hour",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        state_unit=UnitOfVolumetricFlux.INCHES_PER_HOUR,
    ),
    test.case(
        "speed-inches-per-day-none",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfVolumetricFlux.INCHES_PER_DAY,
        state_unit=None,
    ),
    test.case(
        "speed-inches-per-hour-none",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfVolumetricFlux.INCHES_PER_HOUR,
        state_unit=None,
    ),
    test.case(
        "speed-mm-per-second",
        device_class=SensorDeviceClass.SPEED,
        original_unit=UnitOfSpeed.MILLIMETERS_PER_SECOND,
        state_unit=UnitOfSpeed.INCHES_PER_SECOND,
    ),
    test.case(
        "speed-very-fast-none",
        device_class=SensorDeviceClass.SPEED,
        original_unit="very_fast",
        state_unit=None,
    ),
    # Test volume conversion.
    test.case(
        "volume-cubic-meters",
        device_class=SensorDeviceClass.VOLUME,
        original_unit=UnitOfVolume.CUBIC_METERS,
        state_unit=UnitOfVolume.CUBIC_FEET,
    ),
    test.case(
        "volume-liters",
        device_class=SensorDeviceClass.VOLUME,
        original_unit=UnitOfVolume.LITERS,
        state_unit=UnitOfVolume.GALLONS,
    ),
    test.case(
        "volume-milliliters",
        device_class=SensorDeviceClass.VOLUME,
        original_unit=UnitOfVolume.MILLILITERS,
        state_unit=UnitOfVolume.FLUID_OUNCES,
    ),
    test.case(
        "volume-centum-cubic-feet-none",
        device_class=SensorDeviceClass.VOLUME,
        original_unit=UnitOfVolume.CENTUM_CUBIC_FEET,
        state_unit=None,
    ),
    test.case(
        "volume-mille-cubic-feet-none",
        device_class=SensorDeviceClass.VOLUME,
        original_unit=UnitOfVolume.MILLE_CUBIC_FEET,
        state_unit=None,
    ),
    test.case(
        "volume-cubic-feet-none",
        device_class=SensorDeviceClass.VOLUME,
        original_unit=UnitOfVolume.CUBIC_FEET,
        state_unit=None,
    ),
    test.case(
        "volume-fluid-ounces-none",
        device_class=SensorDeviceClass.VOLUME,
        original_unit=UnitOfVolume.FLUID_OUNCES,
        state_unit=None,
    ),
    test.case(
        "volume-gallons-none",
        device_class=SensorDeviceClass.VOLUME,
        original_unit=UnitOfVolume.GALLONS,
        state_unit=None,
    ),
    test.case(
        "volume-very-much-none",
        device_class=SensorDeviceClass.VOLUME,
        original_unit="very_much",
        state_unit=None,
    ),
    # Test water meter conversion.
    test.case(
        "water-cubic-meters",
        device_class=SensorDeviceClass.WATER,
        original_unit=UnitOfVolume.CUBIC_METERS,
        state_unit=UnitOfVolume.CUBIC_FEET,
    ),
    test.case(
        "water-liters",
        device_class=SensorDeviceClass.WATER,
        original_unit=UnitOfVolume.LITERS,
        state_unit=UnitOfVolume.GALLONS,
    ),
    test.case(
        "water-centum-cubic-feet-none",
        device_class=SensorDeviceClass.WATER,
        original_unit=UnitOfVolume.CENTUM_CUBIC_FEET,
        state_unit=None,
    ),
    test.case(
        "water-mille-cubic-feet-none",
        device_class=SensorDeviceClass.WATER,
        original_unit=UnitOfVolume.MILLE_CUBIC_FEET,
        state_unit=None,
    ),
    test.case(
        "water-cubic-feet-none",
        device_class=SensorDeviceClass.WATER,
        original_unit=UnitOfVolume.CUBIC_FEET,
        state_unit=None,
    ),
    test.case(
        "water-gallons-none",
        device_class=SensorDeviceClass.WATER,
        original_unit=UnitOfVolume.GALLONS,
        state_unit=None,
    ),
    test.case(
        "water-very-much-none",
        device_class=SensorDeviceClass.WATER,
        original_unit="very_much",
        state_unit=None,
    ),
    # Test wind speed conversion.
    test.case(
        "wind-meters-per-second",
        device_class=SensorDeviceClass.WIND_SPEED,
        original_unit=UnitOfSpeed.METERS_PER_SECOND,
        state_unit=UnitOfSpeed.MILES_PER_HOUR,
    ),
    test.case(
        "wind-kilometers-per-hour",
        device_class=SensorDeviceClass.WIND_SPEED,
        original_unit=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_unit=UnitOfSpeed.MILES_PER_HOUR,
    ),
    test.case(
        "wind-feet-per-second",
        device_class=SensorDeviceClass.WIND_SPEED,
        original_unit=UnitOfSpeed.FEET_PER_SECOND,
        state_unit=UnitOfSpeed.MILES_PER_HOUR,
    ),
    test.case(
        "wind-knots-none",
        device_class=SensorDeviceClass.WIND_SPEED,
        original_unit=UnitOfSpeed.KNOTS,
        state_unit=None,
    ),
    test.case(
        "wind-miles-per-hour-none",
        device_class=SensorDeviceClass.WIND_SPEED,
        original_unit=UnitOfSpeed.MILES_PER_HOUR,
        state_unit=None,
    ),
    test.case(
        "wind-very-fast-none",
        device_class=SensorDeviceClass.WIND_SPEED,
        original_unit="very_fast",
        state_unit=None,
    ),
)
def get_us_converted_unit(
    device_class: SensorDeviceClass,
    original_unit: str,
    state_unit: str | None,
) -> None:
    """Test unit conversion rules."""
    unit_system = US_CUSTOMARY_SYSTEM
    expect(unit_system.get_converted_unit(device_class, original_unit)).to_equal(
        state_unit
    )


UNCONVERTED_UNITS_US_SYSTEM = {
    SensorDeviceClass.AREA: (
        UnitOfArea.SQUARE_FEET,
        UnitOfArea.SQUARE_INCHES,
        UnitOfArea.SQUARE_MILES,
        UnitOfArea.SQUARE_YARDS,
        UnitOfArea.ACRES,
    ),
    SensorDeviceClass.ATMOSPHERIC_PRESSURE: (UnitOfPressure.INHG,),
    SensorDeviceClass.DISTANCE: (
        UnitOfLength.FEET,
        UnitOfLength.INCHES,
        UnitOfLength.NAUTICAL_MILES,
        UnitOfLength.MILES,
        UnitOfLength.YARDS,
    ),
    SensorDeviceClass.GAS: (
        UnitOfVolume.CENTUM_CUBIC_FEET,
        UnitOfVolume.MILLE_CUBIC_FEET,
        UnitOfVolume.CUBIC_FEET,
    ),
    SensorDeviceClass.PRECIPITATION: (UnitOfLength.INCHES,),
    SensorDeviceClass.PRECIPITATION_INTENSITY: (
        UnitOfVolumetricFlux.INCHES_PER_DAY,
        UnitOfVolumetricFlux.INCHES_PER_HOUR,
    ),
    SensorDeviceClass.PRESSURE: (UnitOfPressure.INHG, UnitOfPressure.PSI),
    SensorDeviceClass.SPEED: (
        UnitOfSpeed.BEAUFORT,
        UnitOfSpeed.FEET_PER_SECOND,
        UnitOfSpeed.KNOTS,
        UnitOfSpeed.MILES_PER_HOUR,
        UnitOfSpeed.INCHES_PER_SECOND,
        UnitOfVolumetricFlux.INCHES_PER_DAY,
        UnitOfVolumetricFlux.INCHES_PER_HOUR,
    ),
    SensorDeviceClass.VOLUME: (
        UnitOfVolume.CENTUM_CUBIC_FEET,
        UnitOfVolume.MILLE_CUBIC_FEET,
        UnitOfVolume.CUBIC_FEET,
        UnitOfVolume.FLUID_OUNCES,
        UnitOfVolume.GALLONS,
    ),
    SensorDeviceClass.WATER: (
        UnitOfVolume.CENTUM_CUBIC_FEET,
        UnitOfVolume.MILLE_CUBIC_FEET,
        UnitOfVolume.CUBIC_FEET,
        UnitOfVolume.GALLONS,
    ),
}


@test.cases(
    test.case(
        "atmospheric-pressure", device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE
    ),
    test.case("distance", device_class=SensorDeviceClass.DISTANCE),
    test.case("gas", device_class=SensorDeviceClass.GAS),
    test.case("precipitation", device_class=SensorDeviceClass.PRECIPITATION),
    test.case(
        "precipitation-intensity",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
    ),
    test.case("pressure", device_class=SensorDeviceClass.PRESSURE),
    test.case("speed", device_class=SensorDeviceClass.SPEED),
    test.case("volume", device_class=SensorDeviceClass.VOLUME),
    test.case("water", device_class=SensorDeviceClass.WATER),
)
def imperial_converted_units(device_class: SensorDeviceClass) -> None:
    """Test unit conversion rules are in place for all units."""
    unit_system = US_CUSTOMARY_SYSTEM
    # Make sure excluded_units is not stale.
    for unit in UNCONVERTED_UNITS_US_SYSTEM[device_class]:
        expect(unit in DEVICE_CLASS_UNITS[device_class]).to_be(True)

    for unit in DEVICE_CLASS_UNITS[device_class]:
        if unit in UNCONVERTED_UNITS_US_SYSTEM[device_class]:
            expect((device_class, unit) not in unit_system._conversions).to_be(True)
            continue
        expect((device_class, unit) in unit_system._conversions).to_be(True)


@test
async def imperial_deprecated_log_warning(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test deprecated imperial unit system logs warning."""
    await async_process_ha_core_config(
        hass,
        {
            "latitude": 60,
            "longitude": 50,
            "elevation": 25,
            "name": "Home",
            "unit_system": "imperial",
            "time_zone": "America/New_York",
            "currency": "USD",
            "country": "US",
            "language": "en",
            "radius": 150,
        },
    )

    expect(hass.config.latitude).to_equal(60)
    expect(hass.config.longitude).to_equal(50)
    expect(hass.config.elevation).to_equal(25)
    expect(hass.config.location_name).to_equal("Home")
    expect(hass.config.units).to_be(US_CUSTOMARY_SYSTEM)
    expect(hass.config.time_zone).to_equal("America/New_York")
    expect(hass.config.currency).to_equal("USD")
    expect(hass.config.country).to_equal("US")
    expect(hass.config.language).to_equal("en")
    expect(hass.config.radius).to_equal(150)
