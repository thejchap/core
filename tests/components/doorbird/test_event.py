"""Tryke skip stub for test_event.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def doorbell_ring_event() -> None:
    """Stub for test_doorbell_ring_event."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def motion_event() -> None:
    """Stub for test_motion_event."""

