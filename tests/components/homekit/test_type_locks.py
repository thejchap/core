"""Tryke skip-stubs for test_type_locks.py - sibling port deferred (436 LOC, 1 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (436 LOC, 1 parametrize)")
async def lock_unlock() -> None:
    """Stub for test_lock_unlock."""

@test.skip("sibling port deferred (436 LOC, 1 parametrize)")
async def no_code() -> None:
    """Stub for test_no_code."""

@test.skip("sibling port deferred (436 LOC, 1 parametrize)")
async def lock_with_linked_doorbell_sensor() -> None:
    """Stub for test_lock_with_linked_doorbell_sensor."""

@test.skip("sibling port deferred (436 LOC, 1 parametrize)")
async def lock_with_linked_doorbell_event() -> None:
    """Stub for test_lock_with_linked_doorbell_event."""

@test.skip("sibling port deferred (436 LOC, 1 parametrize)")
async def lock_with_a_missing_linked_doorbell_sensor() -> None:
    """Stub for test_lock_with_a_missing_linked_doorbell_sensor."""
