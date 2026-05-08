"""Tryke skip-stubs for nest test_diagnostics (port deferred)."""
from tryke import test

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def camera_diagnostics() -> None:
    """Stub for test_camera_diagnostics (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def entry_diagnostics() -> None:
    """Stub for test_entry_diagnostics (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def device_diagnostics() -> None:
    """Stub for test_device_diagnostics (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def setup_susbcriber_failure() -> None:
    """Stub for test_setup_susbcriber_failure (port deferred)."""


