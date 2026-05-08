"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_setup_entry() -> None:
    """Stub for test_async_setup_entry."""

