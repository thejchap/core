"""Test Renault diagnostics. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot; indirect parametrize")
async def entry_diagnostics() -> None:
    """Stub for test_entry_diagnostics (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def device_diagnostics() -> None:
    """Stub for test_device_diagnostics (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def device_diagnostics_invalid_upstream_exception() -> None:
    """Stub for test_device_diagnostics_invalid_upstream_exception (port deferred)."""
