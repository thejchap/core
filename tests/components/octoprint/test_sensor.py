"""Tryke skip-stubs for octoprint test_sensor (port deferred)."""
from tryke import test

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def sensors_printer_disconnected() -> None:
    """Stub for test_sensors_printer_disconnected (port deferred)."""

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def sensors_no_target_temp() -> None:
    """Stub for test_sensors_no_target_temp (port deferred)."""

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def sensors_paused() -> None:
    """Stub for test_sensors_paused (port deferred)."""


