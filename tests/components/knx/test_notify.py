"""Tryke skip-stubs for test_notify.py - sibling port deferred (96 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (96 LOC, 0 parametrize)")
async def notify_simple() -> None:
    """Stub for test_notify_simple."""

@test.skip("sibling port deferred (96 LOC, 0 parametrize)")
async def notify_multiple_sends_with_different_encodings() -> None:
    """Stub for test_notify_multiple_sends_with_different_encodings."""
