"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def dynamic_entities() -> None:
    """Stub for test_dynamic_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def remove_device() -> None:
    """Stub for test_remove_device."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entry_setup_error() -> None:
    """Stub for test_entry_setup_error."""

