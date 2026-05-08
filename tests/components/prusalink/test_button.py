"""Test Prusalink buttons. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def button_pause_cancel() -> None:
    """Stub for test_button_pause_cancel (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def button_resume_cancel() -> None:
    """Stub for test_button_resume_cancel (port deferred)."""
