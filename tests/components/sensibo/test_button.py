"""The test for the sensibo button platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def button() -> None:
    """Stub for test_button (port deferred)."""

@test.skip("syrupy snapshot")
async def button_update() -> None:
    """Stub for test_button_update (port deferred)."""

@test.skip("syrupy snapshot")
async def button_failure() -> None:
    """Stub for test_button_failure (port deferred)."""
