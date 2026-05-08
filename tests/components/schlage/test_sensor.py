"""Test schlage sensor. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def battery_sensor() -> None:
    """Stub for test_battery_sensor (port deferred)."""
