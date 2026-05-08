"""Test the switchbot fan. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def circulator_fan_controlling() -> None:
    """Stub for test_circulator_fan_controlling (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def air_purifier_controlling() -> None:
    """Stub for test_air_purifier_controlling (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def exception_handling_air_purifier_service() -> None:
    """Stub for test_exception_handling_air_purifier_service (port deferred)."""
