"""Tests for the Rova integration init. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def reload() -> None:
    """Stub for test_reload (port deferred)."""

@test.skip("syrupy snapshot")
async def service() -> None:
    """Stub for test_service (port deferred)."""

@test.skip("syrupy snapshot")
async def retry_after_failure() -> None:
    """Stub for test_retry_after_failure (port deferred)."""

@test.skip("syrupy snapshot")
async def issue_if_not_rova_area() -> None:
    """Stub for test_issue_if_not_rova_area (port deferred)."""
