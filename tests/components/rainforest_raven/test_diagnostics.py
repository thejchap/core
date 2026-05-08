"""Test the Rainforest Eagle diagnostics. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def entry_diagnostics_no_meters() -> None:
    """Stub for test_entry_diagnostics_no_meters (port deferred)."""

@test.skip("syrupy snapshot")
async def entry_diagnostics() -> None:
    """Stub for test_entry_diagnostics (port deferred)."""
