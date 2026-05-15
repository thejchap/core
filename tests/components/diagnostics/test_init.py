"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def websocket() -> None:
    """Stub for test_websocket (port deferred)."""

@test.skip("pending tryke port")
async def download_diagnostics() -> None:
    """Stub for test_download_diagnostics (port deferred)."""

@test.skip("pending tryke port")
async def download_diagnostics_requires_admin() -> None:
    """Stub for test_download_diagnostics_requires_admin (port deferred)."""

@test.skip("pending tryke port")
async def failure_scenarios() -> None:
    """Stub for test_failure_scenarios (port deferred)."""
