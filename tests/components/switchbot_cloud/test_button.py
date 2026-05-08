"""Test for the switchbot_cloud bot as a button. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def pressmode_bot() -> None:
    """Stub for test_pressmode_bot (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def switchmode_bot_no_button_entity() -> None:
    """Stub for test_switchmode_bot_no_button_entity (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def loaded_buttons() -> None:
    """Stub for test_loaded_buttons (port deferred)."""
