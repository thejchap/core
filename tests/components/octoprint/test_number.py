"""Tryke skip-stubs for octoprint test_number (port deferred)."""
from tryke import test

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def numbers_printer_disconnected() -> None:
    """Stub for test_numbers_printer_disconnected (port deferred)."""

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def numbers() -> None:
    """Stub for test_numbers (port deferred)."""

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def numbers_no_target_temp() -> None:
    """Stub for test_numbers_no_target_temp (port deferred)."""

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def set_tool_temp() -> None:
    """Stub for test_set_tool_temp (port deferred)."""

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def set_bed_temp() -> None:
    """Stub for test_set_bed_temp (port deferred)."""

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def set_tool_n_temp() -> None:
    """Stub for test_set_tool_n_temp (port deferred)."""


