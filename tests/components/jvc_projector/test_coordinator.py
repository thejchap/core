"""Tryke skip-stubs for test_coordinator.py - indirect parametrize unsupported."""

from tryke import test

@test.skip("indirect parametrize unsupported")
async def coordinator_update() -> None:
    """Stub for test_coordinator_update."""

@test.skip("indirect parametrize unsupported")
async def coordinator_device_on() -> None:
    """Stub for test_coordinator_device_on."""

@test.skip("indirect parametrize unsupported")
async def coordinator_setup_connect_error() -> None:
    """Stub for test_coordinator_setup_connect_error."""

@test.skip("indirect parametrize unsupported")
async def coordinator_setup_power_command_error() -> None:
    """Stub for test_coordinator_setup_power_command_error."""

@test.skip("indirect parametrize unsupported")
async def coordinator_command_error_keeps_other_entities_available() -> None:
    """Stub for test_coordinator_command_error_keeps_other_entities_available."""
