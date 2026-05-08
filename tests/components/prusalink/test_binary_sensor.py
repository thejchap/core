"""Test Prusalink sensors. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def binary_sensors_no_job() -> None:
    """Stub for test_binary_sensors_no_job (port deferred)."""
