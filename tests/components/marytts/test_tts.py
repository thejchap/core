"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup_component() -> None:
    """Stub for test_setup_component (port deferred)."""

@test.skip("pending tryke port")
async def service_say() -> None:
    """Stub for test_service_say (port deferred)."""

@test.skip("pending tryke port")
async def service_say_with_effect() -> None:
    """Stub for test_service_say_with_effect (port deferred)."""

@test.skip("pending tryke port")
async def service_say_http_error() -> None:
    """Stub for test_service_say_http_error (port deferred)."""
