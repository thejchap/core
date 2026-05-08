"""Tests for the Slide Local switch platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def all_entities() -> None:
    """Stub for test_all_entities (port deferred)."""

@test.skip("syrupy snapshot")
async def services() -> None:
    """Stub for test_services (port deferred)."""

@test.skip("syrupy snapshot")
async def service_exception() -> None:
    """Stub for test_service_exception (port deferred)."""
