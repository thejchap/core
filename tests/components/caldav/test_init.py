"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def load_unload() -> None:
    """Stub for test_load_unload."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def client_failure() -> None:
    """Stub for test_client_failure."""

