"""Tests for Renault sensors. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("snapshot test — out of scope")
async def device_trackers() -> None:
    """Stub for test_device_trackers (port deferred)."""

@test.skip("snapshot test — out of scope")
async def device_tracker_empty() -> None:
    """Stub for test_device_tracker_empty (port deferred)."""

@test.skip("snapshot test — out of scope")
async def device_tracker_errors() -> None:
    """Stub for test_device_tracker_errors (port deferred)."""

@test.skip("snapshot test — out of scope")
async def device_tracker_access_denied() -> None:
    """Stub for test_device_tracker_access_denied (port deferred)."""

@test.skip("snapshot test — out of scope")
async def device_tracker_not_supported() -> None:
    """Stub for test_device_tracker_not_supported (port deferred)."""
