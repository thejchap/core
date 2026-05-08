"""Tryke skip-stubs for nest test_api (port deferred)."""
from tryke import test

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def auth() -> None:
    """Stub for test_auth (port deferred)."""


