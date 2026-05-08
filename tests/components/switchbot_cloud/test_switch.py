"""Test for the switchbot_cloud relay switch & bot. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def relay_switch() -> None:
    """Stub for test_relay_switch (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def switchmode_bot() -> None:
    """Stub for test_switchmode_bot (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def pressmode_bot_no_switch_entity() -> None:
    """Stub for test_pressmode_bot_no_switch_entity (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def switch_relay_2pm_turn_on() -> None:
    """Stub for test_switch_relay_2pm_turn_on (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def switch_relay_2pm_turn_off() -> None:
    """Stub for test_switch_relay_2pm_turn_off (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def switch_relay_2pm_coordination_is_none() -> None:
    """Stub for test_switch_relay_2pm_coordination_is_none (port deferred)."""
