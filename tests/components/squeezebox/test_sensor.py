"""Test squeezebox sensors. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def server_sensor() -> None:
    """Stub for test_server_sensor (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def player_sensor_next_alarm() -> None:
    """Stub for test_player_sensor_next_alarm (port deferred)."""
