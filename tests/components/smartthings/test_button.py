"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def all_entities() -> None:
    """Stub for test_all_entities (port deferred)."""

@test.skip("snapshot test - port deferred")
async def press() -> None:
    """Stub for test_press (port deferred)."""

@test.skip("snapshot test - port deferred")
async def availability() -> None:
    """Stub for test_availability (port deferred)."""

@test.skip("snapshot test - port deferred")
async def availability_at_start() -> None:
    """Stub for test_availability_at_start (port deferred)."""

@test.skip("snapshot test - port deferred")
async def turn_on_without_remote_control() -> None:
    """Stub for test_turn_on_without_remote_control (port deferred)."""

@test.skip("snapshot test - port deferred")
async def turn_on_with_wrong_dishwasher_machine_state() -> None:
    """Stub for test_turn_on_with_wrong_dishwasher_machine_state (port deferred)."""
