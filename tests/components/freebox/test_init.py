"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_import() -> None:
    """Stub for test_setup_import."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_remove() -> None:
    """Stub for test_unload_remove."""

