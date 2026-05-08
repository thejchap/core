"""Tryke skip-stubs for teslemetry/test_button.py."""

from tryke import test


@test.skip("requires teslemetry API + snapshot — port deferred")
async def button() -> None:
    """Stub for test_button."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def press() -> None:
    """Stub for test_press."""

