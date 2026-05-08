"""Test update platform for Swing2Sleep Smarla integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def update() -> None:
    """Stub for test_update (port deferred)."""

@test.skip("syrupy snapshot")
async def update_available() -> None:
    """Stub for test_update_available (port deferred)."""

@test.skip("syrupy snapshot")
async def update_install() -> None:
    """Stub for test_update_install (port deferred)."""

@test.skip("syrupy snapshot")
async def update_in_progress() -> None:
    """Stub for test_update_in_progress (port deferred)."""

@test.skip("syrupy snapshot")
async def update_unknown() -> None:
    """Stub for test_update_unknown (port deferred)."""
