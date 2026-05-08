"""Tryke skip-stubs for octoprint test_binary_sensor (port deferred)."""
from tryke import test

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def sensors_printer_offline() -> None:
    """Stub for test_sensors_printer_offline (port deferred)."""

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""


