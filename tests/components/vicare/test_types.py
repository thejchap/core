"""Test ViCare diagnostics."""

from tryke import expect, test

from homeassistant.components.climate import PRESET_COMFORT, PRESET_SLEEP
from homeassistant.components.vicare.fan import VentilationMode
from homeassistant.components.vicare.types import HeatingProgram


@test.cases(
    test.case("empty", vicare_program="", expected_result=None),
    test.case("none", vicare_program=None, expected_result=None),
    test.case("anything", vicare_program="anything", expected_result=None),
    test.case("comfort", vicare_program=HeatingProgram.COMFORT, expected_result=PRESET_COMFORT),
    test.case("comfort_heating", vicare_program=HeatingProgram.COMFORT_HEATING, expected_result=PRESET_COMFORT),
)
async def heating_program_to_ha_preset(
    vicare_program: str | None,
    expected_result: str | None,
) -> None:
    """Testing ViCare HeatingProgram to HA Preset."""
    expect(HeatingProgram.to_ha_preset(vicare_program)).to_equal(expected_result)


@test.cases(
    test.case("empty", ha_preset="", expected_result=None),
    test.case("none", ha_preset=None, expected_result=None),
    test.case("anything", ha_preset="anything", expected_result=None),
    test.case("sleep", ha_preset=PRESET_SLEEP, expected_result=HeatingProgram.REDUCED),
)
async def ha_preset_to_heating_program(
    ha_preset: str | None,
    expected_result: str | None,
) -> None:
    """Testing HA Preset to ViCare HeatingProgram."""
    supported_programs = [
        HeatingProgram.COMFORT,
        HeatingProgram.ECO,
        HeatingProgram.NORMAL,
        HeatingProgram.REDUCED,
    ]
    expect(HeatingProgram.from_ha_preset(ha_preset, supported_programs)).to_equal(
        expected_result
    )


@test
async def ha_preset_to_heating_program_error() -> None:
    """Testing HA Preset to ViCare HeatingProgram."""
    supported_programs = ["test"]
    expect(
        HeatingProgram.from_ha_preset(HeatingProgram.NORMAL, supported_programs)
    ).to_be_none()


@test.cases(
    test.case("empty", vicare_mode="", expected_result=None),
    test.case("none", vicare_mode=None, expected_result=None),
    test.case("anything", vicare_mode="anything", expected_result=None),
    test.case(
        "sensor_override",
        vicare_mode="sensorOverride",
        expected_result=VentilationMode.SENSOR_OVERRIDE,
    ),
)
async def ventilation_mode_to_ha_mode(
    vicare_mode: str | None,
    expected_result: str | None,
) -> None:
    """Testing ViCare mode to VentilationMode."""
    expect(VentilationMode.from_vicare_mode(vicare_mode)).to_equal(expected_result)


@test.cases(
    test.case("empty", ha_mode="", expected_result=None),
    test.case("none", ha_mode=None, expected_result=None),
    test.case("anything", ha_mode="anything", expected_result=None),
    test.case(
        "sensor_override",
        ha_mode=VentilationMode.SENSOR_OVERRIDE,
        expected_result="sensorOverride",
    ),
)
async def ha_mode_to_ventilation_mode(
    ha_mode: str | None,
    expected_result: str | None,
) -> None:
    """Testing VentilationMode to ViCare mode."""
    expect(VentilationMode.to_vicare_mode(ha_mode)).to_equal(expected_result)
