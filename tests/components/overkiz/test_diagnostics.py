"""Tryke skip-stubs for overkiz diagnostics tests.

Original tests use OverkizClient API mocks + token refresh; full port deferred.
"""

from tryke import test

@test.skip("OverkizClient API mocks + token refresh")
async def diagnostics() -> None:
    """Test diagnostics."""

@test.skip("OverkizClient API mocks + token refresh")
async def device_diagnostics() -> None:
    """Test device diagnostics."""

@test.skip("OverkizClient API mocks + token refresh")
async def device_diagnostics_execution_history_subsystem() -> None:
    """Test execution history matching ignores subsystem suffix."""
