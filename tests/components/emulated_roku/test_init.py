"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config_required_fields() -> None:
    """Stub for test_config_required_fields."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config_already_registered_not_configured() -> None:
    """Stub for test_config_already_registered_not_configured."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_entry_successful() -> None:
    """Stub for test_setup_entry_successful."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""

