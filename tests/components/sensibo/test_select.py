"""The test for the sensibo select platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def select() -> None:
    """Stub for test_select (port deferred)."""

@test.skip("syrupy snapshot")
async def select_set_option() -> None:
    """Stub for test_select_set_option (port deferred)."""
