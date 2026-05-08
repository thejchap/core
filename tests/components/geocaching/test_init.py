"""Tryke skip stubs for test_init - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def oauth_implementation_not_available() -> None:
    """Stub for test_oauth_implementation_not_available (port deferred)."""


