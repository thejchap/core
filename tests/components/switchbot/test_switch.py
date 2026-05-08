"""Test the switchbot switches. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def switchbot_switch_with_restore_state() -> None:
    """Stub for test_switchbot_switch_with_restore_state (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def exception_handling_switch() -> None:
    """Stub for test_exception_handling_switch (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def relay_switch_control() -> None:
    """Stub for test_relay_switch_control (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def relay_switch_2pm_control() -> None:
    """Stub for test_relay_switch_2pm_control (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def relay_switch_control_with_exception() -> None:
    """Stub for test_relay_switch_control_with_exception (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def air_purifier_switch_control() -> None:
    """Stub for test_air_purifier_switch_control (port deferred)."""
