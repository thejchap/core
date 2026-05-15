"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def cached_event_message() -> None:
    """Stub for test_cached_event_message (port deferred)."""

@test.skip("pending tryke port")
async def cached_event_message_with_different_idens() -> None:
    """Stub for test_cached_event_message_with_different_idens (port deferred)."""

@test.skip("pending tryke port")
async def state_diff_event() -> None:
    """Stub for test_state_diff_event (port deferred)."""

@test.skip("pending tryke port")
async def message_to_json_bytes() -> None:
    """Stub for test_message_to_json_bytes (port deferred)."""
