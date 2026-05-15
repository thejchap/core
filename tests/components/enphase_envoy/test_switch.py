"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def switch() -> None:
    """Stub for test_switch (port deferred)."""

@test.skip("snapshot test - port deferred")
async def no_switch() -> None:
    """Stub for test_no_switch (port deferred)."""

@test.skip("snapshot test - port deferred")
async def switch_grid_operation() -> None:
    """Stub for test_switch_grid_operation (port deferred)."""

@test.skip("snapshot test - port deferred")
async def switch_grid_operation_with_error() -> None:
    """Stub for test_switch_grid_operation_with_error (port deferred)."""

@test.skip("snapshot test - port deferred")
async def switch_charge_from_grid_operation() -> None:
    """Stub for test_switch_charge_from_grid_operation (port deferred)."""

@test.skip("snapshot test - port deferred")
async def switch_charge_from_grid_operation_with_error() -> None:
    """Stub for test_switch_charge_from_grid_operation_with_error (port deferred)."""

@test.skip("snapshot test - port deferred")
async def switch_relay_operation() -> None:
    """Stub for test_switch_relay_operation (port deferred)."""

@test.skip("snapshot test - port deferred")
async def switch_relay_operation_with_error() -> None:
    """Stub for test_switch_relay_operation_with_error (port deferred)."""
