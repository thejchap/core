"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def switches() -> None:
    """Stub for test_switches (port deferred)."""

@test.skip("snapshot test - port deferred")
async def update_success() -> None:
    """Stub for test_update_success (port deferred)."""

@test.skip("snapshot test - port deferred")
async def update_failed() -> None:
    """Stub for test_update_failed (port deferred)."""

@test.skip("snapshot test - port deferred")
async def a01_switch_success() -> None:
    """Stub for test_a01_switch_success (port deferred)."""

@test.skip("snapshot test - port deferred")
async def a01_switch_failure() -> None:
    """Stub for test_a01_switch_failure (port deferred)."""

@test.skip("snapshot test - port deferred")
async def a01_switch_unknown_state() -> None:
    """Stub for test_a01_switch_unknown_state (port deferred)."""
