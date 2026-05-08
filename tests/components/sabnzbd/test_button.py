"""Button tests for the SABnzbd component. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def button_setup() -> None:
    """Stub for test_button_setup (port deferred)."""

@test.skip("syrupy snapshot")
async def button_presses() -> None:
    """Stub for test_button_presses (port deferred)."""

@test.skip("syrupy snapshot")
async def buttons_exception() -> None:
    """Stub for test_buttons_exception (port deferred)."""

@test.skip("syrupy snapshot")
async def buttons_unavailable() -> None:
    """Stub for test_buttons_unavailable (port deferred)."""
