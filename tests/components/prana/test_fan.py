"""Integration-style tests for Prana fans. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def fans() -> None:
    """Stub for test_fans (port deferred)."""

@test.skip("syrupy snapshot")
async def fans_turn_on_off() -> None:
    """Stub for test_fans_turn_on_off (port deferred)."""

@test.skip("syrupy snapshot")
async def fans_set_percentage() -> None:
    """Stub for test_fans_set_percentage (port deferred)."""

@test.skip("syrupy snapshot")
async def fans_set_preset_mode() -> None:
    """Stub for test_fans_set_preset_mode (port deferred)."""
