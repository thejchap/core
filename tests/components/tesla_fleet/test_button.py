"""Tryke skip-stubs for tesla_fleet/test_button.py."""

from tryke import test


@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def button() -> None:
    """Stub for test_button."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def press() -> None:
    """Stub for test_press."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def press_signing_error() -> None:
    """Stub for test_press_signing_error."""

