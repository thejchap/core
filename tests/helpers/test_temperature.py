"""Tests Home Assistant temperature helpers."""

from tryke import Depends, expect, fixture, test

from homeassistant.const import (
    PRECISION_HALVES,
    PRECISION_TENTHS,
    PRECISION_WHOLE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.temperature import display_temp

from tests.hass_fixtures import hass

TEMP = 24.636626


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path.

    Required so imported fixtures resolved via ``Depends(...)`` actually
    execute (Tryke only wires Depends resolution for modules that
    statically declare at least one ``@fixture``).
    """
    return 0


@test
async def temperature_not_a_number(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that temperature is a number."""
    temp = "Temperature"
    caught: Exception | None = None
    try:
        display_temp(hass, temp, UnitOfTemperature.CELSIUS, PRECISION_HALVES)
    except Exception as exc:  # noqa: BLE001
        caught = exc
    expect(caught).not_.to_be_none()
    expect(f"Temperature is not a number: {temp}" in str(caught)).to_be(True)


@test
async def celsius_halves(hass: HomeAssistant = Depends(hass)) -> None:
    """Test temperature to celsius rounding to halves."""
    expect(
        display_temp(hass, TEMP, UnitOfTemperature.CELSIUS, PRECISION_HALVES)
    ).to_equal(24.5)


@test
async def celsius_tenths(hass: HomeAssistant = Depends(hass)) -> None:
    """Test temperature to celsius rounding to tenths."""
    expect(
        display_temp(hass, TEMP, UnitOfTemperature.CELSIUS, PRECISION_TENTHS)
    ).to_equal(24.6)


@test
async def fahrenheit_wholes(hass: HomeAssistant = Depends(hass)) -> None:
    """Test temperature to fahrenheit rounding to wholes."""
    expect(
        display_temp(hass, TEMP, UnitOfTemperature.FAHRENHEIT, PRECISION_WHOLE)
    ).to_equal(-4)
