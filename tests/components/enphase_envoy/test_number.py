"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def number() -> None:
    """Stub for test_number (port deferred)."""

@test.skip("snapshot test - port deferred")
async def no_number() -> None:
    """Stub for test_no_number (port deferred)."""

@test.skip("snapshot test - port deferred")
async def number_operation_storage() -> None:
    """Stub for test_number_operation_storage (port deferred)."""

@test.skip("snapshot test - port deferred")
async def number_operation_storage_with_error() -> None:
    """Stub for test_number_operation_storage_with_error (port deferred)."""

@test.skip("snapshot test - port deferred")
async def number_operation_relays() -> None:
    """Stub for test_number_operation_relays (port deferred)."""

@test.skip("snapshot test - port deferred")
async def number_operation_relays_with_error() -> None:
    """Stub for test_number_operation_relays_with_error (port deferred)."""
