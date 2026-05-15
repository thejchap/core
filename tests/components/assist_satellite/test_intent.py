"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def broadcast_intent() -> None:
    """Stub for test_broadcast_intent (port deferred)."""

@test.skip("pending tryke port")
async def broadcast_intent_excluded_domains() -> None:
    """Stub for test_broadcast_intent_excluded_domains (port deferred)."""
