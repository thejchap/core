"""Tryke skip-stubs for nest test_device_info (port deferred)."""
from tryke import test

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def device_custom_name() -> None:
    """Stub for test_device_custom_name (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def device_name_room() -> None:
    """Stub for test_device_name_room (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def device_no_name() -> None:
    """Stub for test_device_no_name (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def device_invalid_type() -> None:
    """Stub for test_device_invalid_type (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def suggested_area() -> None:
    """Stub for test_suggested_area (port deferred)."""


