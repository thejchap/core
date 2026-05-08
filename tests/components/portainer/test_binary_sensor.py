"""Tests for the Portainer binary sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def all_entities() -> None:
    """Stub for test_all_entities (port deferred)."""

@test.skip("syrupy snapshot")
async def refresh_endpoints_exceptions() -> None:
    """Stub for test_refresh_endpoints_exceptions (port deferred)."""

@test.skip("syrupy snapshot")
async def refresh_containers_exceptions() -> None:
    """Stub for test_refresh_containers_exceptions (port deferred)."""
