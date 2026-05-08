"""Tryke skip-stubs for opendisplay event tests."""

from tryke import test


@test.skip("bluetooth-stack tests — fixtures not in shim")
async def event_placeholder() -> None:
    """Placeholder skipped sibling tests for test_event.py."""
