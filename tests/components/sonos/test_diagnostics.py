"""Tests for the diagnostics data provided by the Sonos integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def diagnostics_config_entry() -> None:
    """Stub for test_diagnostics_config_entry (port deferred)."""

@test.skip("syrupy snapshot")
async def diagnostics_device() -> None:
    """Stub for test_diagnostics_device (port deferred)."""
