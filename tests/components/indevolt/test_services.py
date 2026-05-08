"""Tryke skip-stubs for test_services.py - indirect parametrize unsupported."""

from tryke import test

@test.skip("indirect parametrize unsupported")
async def service_charge_discharge() -> None:
    """Stub for test_service_charge_discharge."""

@test.skip("indirect parametrize unsupported")
async def service_power_too_high() -> None:
    """Stub for test_service_power_too_high."""

@test.skip("indirect parametrize unsupported")
async def service_target_soc_below_minimum() -> None:
    """Stub for test_service_target_soc_below_minimum."""

@test.skip("indirect parametrize unsupported")
async def service_target_soc_below_emergency() -> None:
    """Stub for test_service_target_soc_below_emergency."""

@test.skip("indirect parametrize unsupported")
async def service_missing_target() -> None:
    """Stub for test_service_missing_target."""

@test.skip("indirect parametrize unsupported")
async def multi_device_partial_validation_failure() -> None:
    """Stub for test_multi_device_partial_validation_failure."""

@test.skip("indirect parametrize unsupported")
async def multi_device_full_validation_failure() -> None:
    """Stub for test_multi_device_full_validation_failure."""

@test.skip("indirect parametrize unsupported")
async def charge_outdoor_portable() -> None:
    """Stub for test_charge_outdoor_portable."""

@test.skip("indirect parametrize unsupported")
async def service_charge_missing_energy_mode() -> None:
    """Stub for test_service_charge_missing_energy_mode."""

@test.skip("indirect parametrize unsupported")
async def single_device_execution_failure() -> None:
    """Stub for test_single_device_execution_failure."""

@test.skip("indirect parametrize unsupported")
async def multi_device_execution_failure() -> None:
    """Stub for test_multi_device_execution_failure."""
