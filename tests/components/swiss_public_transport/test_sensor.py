"""Tests for the swiss_public_transport sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def all_entities() -> None:
    """Stub for test_all_entities (port deferred)."""

@test.skip("syrupy snapshot")
async def fetching_data() -> None:
    """Stub for test_fetching_data (port deferred)."""

@test.skip("syrupy snapshot")
async def fetching_data_setup_exception() -> None:
    """Stub for test_fetching_data_setup_exception (port deferred)."""
