"""Tryke skip stub for test_setup.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_connect_error() -> None:
    """Stub for test_setup_connect_error."""

