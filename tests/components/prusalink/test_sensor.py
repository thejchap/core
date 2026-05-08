"""Test Prusalink sensors. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def sensors_no_job() -> None:
    """Stub for test_sensors_no_job (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def sensors_idle_job_mk3() -> None:
    """Stub for test_sensors_idle_job_mk3 (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def sensors_active_job() -> None:
    """Stub for test_sensors_active_job (port deferred)."""
