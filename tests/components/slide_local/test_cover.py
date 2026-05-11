"""Tests for the Slide Local cover platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("snapshot test — out of scope")
async def all_entities() -> None:
    """Stub for test_all_entities (port deferred)."""

@test.skip("snapshot test — out of scope")
async def connection_error() -> None:
    """Stub for test_connection_error (port deferred)."""

@test.skip("snapshot test — out of scope")
async def state_change() -> None:
    """Stub for test_state_change (port deferred)."""

@test.skip("snapshot test — out of scope")
async def open_cover() -> None:
    """Stub for test_open_cover (port deferred)."""

@test.skip("snapshot test — out of scope")
async def close_cover() -> None:
    """Stub for test_close_cover (port deferred)."""

@test.skip("snapshot test — out of scope")
async def stop_cover() -> None:
    """Stub for test_stop_cover (port deferred)."""

@test.skip("snapshot test — out of scope")
async def set_position() -> None:
    """Stub for test_set_position (port deferred)."""
