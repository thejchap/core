"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_unload_config_entry() -> None:
    """Stub for test_load_unload_config_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def invalid_auth() -> None:
    """Stub for test_invalid_auth."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def devices_in_dr() -> None:
    """Stub for test_devices_in_dr."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def all_entities_loaded() -> None:
    """Stub for test_all_entities_loaded."""

