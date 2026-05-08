"""Test Snoo Events. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def events() -> None:
    """Stub for test_events (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def events_data_on_startup() -> None:
    """Stub for test_events_data_on_startup (port deferred)."""
