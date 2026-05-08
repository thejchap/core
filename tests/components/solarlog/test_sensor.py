"""Test the Home Assistant solarlog sensor module. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def all_entities() -> None:
    """Stub for test_all_entities (port deferred)."""

@test.skip("syrupy snapshot")
async def add_remove_entities() -> None:
    """Stub for test_add_remove_entities (port deferred)."""

@test.skip("syrupy snapshot")
async def connection_error() -> None:
    """Stub for test_connection_error (port deferred)."""
