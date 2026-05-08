"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_unload_config_entry() -> None:
    """Stub for test_load_unload_config_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migration_from_v1() -> None:
    """Stub for test_migration_from_v1."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migration_from_v2() -> None:
    """Stub for test_migration_from_v2."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_entry_no_planes() -> None:
    """Stub for test_setup_entry_no_planes."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_entry_multiple_planes_no_api_key() -> None:
    """Stub for test_setup_entry_multiple_planes_no_api_key."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_multi_plane_initialization() -> None:
    """Stub for test_coordinator_multi_plane_initialization."""

