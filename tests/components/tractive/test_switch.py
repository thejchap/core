"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def switch() -> None:
    """Stub for test_switch (port deferred)."""

@test.skip("snapshot test - port deferred")
async def switch_on() -> None:
    """Stub for test_switch_on (port deferred)."""

@test.skip("snapshot test - port deferred")
async def switch_off() -> None:
    """Stub for test_switch_off (port deferred)."""

@test.skip("snapshot test - port deferred")
async def live_tracking_switch() -> None:
    """Stub for test_live_tracking_switch (port deferred)."""

@test.skip("snapshot test - port deferred")
async def switch_on_with_exception() -> None:
    """Stub for test_switch_on_with_exception (port deferred)."""

@test.skip("snapshot test - port deferred")
async def switch_off_with_exception() -> None:
    """Stub for test_switch_off_with_exception (port deferred)."""

@test.skip("snapshot test - port deferred")
async def switch_unavailable() -> None:
    """Stub for test_switch_unavailable (port deferred)."""
