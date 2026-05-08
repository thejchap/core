"""The tests for the button component. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def state() -> None:
    """Stub for test_state (port deferred)."""

@test.skip("syrupy snapshot")
async def button_press() -> None:
    """Stub for test_button_press (port deferred)."""

@test.skip("syrupy snapshot")
async def button_press_errors() -> None:
    """Stub for test_button_press_errors (port deferred)."""
