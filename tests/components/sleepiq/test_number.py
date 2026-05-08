"""The tests for SleepIQ number platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def firmness() -> None:
    """Stub for test_firmness (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def actuators() -> None:
    """Stub for test_actuators (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def foot_warmer_timer() -> None:
    """Stub for test_foot_warmer_timer (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def core_climate_timer() -> None:
    """Stub for test_core_climate_timer (port deferred)."""
