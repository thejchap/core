"""The tests for SleepIQ binary sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def button_calibrate() -> None:
    """Stub for test_button_calibrate (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def button_stop_pump() -> None:
    """Stub for test_button_stop_pump (port deferred)."""
