"""Tryke skip-stubs for test_climate.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def no_thermostat_options() -> None:
    """Stub for test_no_thermostat_options."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def static_attributes() -> None:
    """Stub for test_static_attributes."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def dynamic_attributes() -> None:
    """Stub for test_dynamic_attributes."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def mode_service_calls() -> None:
    """Stub for test_mode_service_calls."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def fan_modes_service_calls() -> None:
    """Stub for test_fan_modes_service_calls."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def service_calls_off_mode() -> None:
    """Stub for test_service_calls_off_mode."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def service_calls_cool_mode() -> None:
    """Stub for test_service_calls_cool_mode."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def service_calls_heat_mode() -> None:
    """Stub for test_service_calls_heat_mode."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def service_calls_auto_mode() -> None:
    """Stub for test_service_calls_auto_mode."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def async_update_errors() -> None:
    """Stub for test_async_update_errors."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def unique_id() -> None:
    """Stub for test_unique_id."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def preset_mode() -> None:
    """Stub for test_preset_mode."""
