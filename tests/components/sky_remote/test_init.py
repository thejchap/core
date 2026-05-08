"""Tests for the Sky Remote component. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_entry() -> None:
    """Stub for test_setup_entry (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_unconnectable_entry() -> None:
    """Stub for test_setup_unconnectable_entry (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry (port deferred)."""
