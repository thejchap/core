"""Test Prusalink camera. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def camera_no_job() -> None:
    """Stub for test_camera_no_job (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def camera_idle_job_mk3() -> None:
    """Stub for test_camera_idle_job_mk3 (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def camera_active_job() -> None:
    """Stub for test_camera_active_job (port deferred)."""
