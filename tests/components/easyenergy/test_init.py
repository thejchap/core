"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_unload_config_entry() -> None:
    """Stub for test_load_unload_config_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config_flow_entry_not_ready() -> None:
    """Stub for test_config_flow_entry_not_ready."""

