"""Test squeezebox binary sensors. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def binary_server_sensor() -> None:
    """Stub for test_binary_server_sensor (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def player_alarm_sensors_device_class() -> None:
    """Stub for test_player_alarm_sensors_device_class (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def player_alarm_sensors_state() -> None:
    """Stub for test_player_alarm_sensors_state (port deferred)."""
