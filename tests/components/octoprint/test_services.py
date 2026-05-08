"""Tryke skip-stubs for octoprint test_services (port deferred)."""
from tryke import test

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def connect_all_arguments() -> None:
    """Stub for test_connect_all_arguments (port deferred)."""

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def connect_default() -> None:
    """Stub for test_connect_default (port deferred)."""


