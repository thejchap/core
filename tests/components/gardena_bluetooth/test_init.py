"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_delayed_product() -> None:
    """Stub for test_setup_delayed_product."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_retry() -> None:
    """Stub for test_setup_retry."""

