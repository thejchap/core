"""Test Qbus cover entities. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def cover_up_down_stop() -> None:
    """Stub for test_cover_up_down_stop (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def cover_position() -> None:
    """Stub for test_cover_position (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def cover_slats() -> None:
    """Stub for test_cover_slats (port deferred)."""
