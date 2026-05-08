"""Test pushbullet sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def sensor_truncation_logic() -> None:
    """Stub for test_sensor_truncation_logic (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def sensor_truncation_title_sensor() -> None:
    """Stub for test_sensor_truncation_title_sensor (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def sensor_truncation_non_string_handling() -> None:
    """Stub for test_sensor_truncation_non_string_handling (port deferred)."""
