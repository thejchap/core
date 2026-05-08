"""Test the switchbot covers. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def curtain3_setup() -> None:
    """Stub for test_curtain3_setup (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def curtain3_controlling() -> None:
    """Stub for test_curtain3_controlling (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def curtain3_custom_speed_controlling() -> None:
    """Stub for test_curtain3_custom_speed_controlling (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def blindtilt_setup() -> None:
    """Stub for test_blindtilt_setup (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def blindtilt_controlling() -> None:
    """Stub for test_blindtilt_controlling (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def roller_shade_setup() -> None:
    """Stub for test_roller_shade_setup (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def roller_shade_controlling() -> None:
    """Stub for test_roller_shade_controlling (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def exception_handling_cover_service() -> None:
    """Stub for test_exception_handling_cover_service (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def garage_door_opener_controlling() -> None:
    """Stub for test_garage_door_opener_controlling (port deferred)."""
