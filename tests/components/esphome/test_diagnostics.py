"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def diagnostics() -> None:
    """Stub for test_diagnostics (port deferred)."""

@test.skip("snapshot test - port deferred")
async def diagnostics_with_dashboard_data() -> None:
    """Stub for test_diagnostics_with_dashboard_data (port deferred)."""

@test.skip("snapshot test - port deferred")
async def diagnostics_with_bluetooth() -> None:
    """Stub for test_diagnostics_with_bluetooth (port deferred)."""
