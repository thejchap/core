"""Test init of Solarman integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("indirect parametrize")
async def load_unload() -> None:
    """Stub for test_load_unload (port deferred)."""

@test.skip("indirect parametrize")
async def load_failure() -> None:
    """Stub for test_load_failure (port deferred)."""
