"""The tests for the Season integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def season_northern_hemisphere() -> None:
    """Stub for test_season_northern_hemisphere (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def season_southern_hemisphere() -> None:
    """Stub for test_season_southern_hemisphere (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def season_equator() -> None:
    """Stub for test_season_equator (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def season_local_midnight() -> None:
    """Stub for test_season_local_midnight (port deferred)."""
