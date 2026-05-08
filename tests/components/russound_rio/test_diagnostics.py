"""Tests for the diagnostics data provided by the Russound RIO integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def entry_diagnostics() -> None:
    """Stub for test_entry_diagnostics (port deferred)."""
