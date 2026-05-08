"""Tryke skip stubs for test_light - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_setup() -> None:
    """Stub for test_light_setup (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_config_entry() -> None:
    """Stub for test_unload_config_entry (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def remove_config_entry() -> None:
    """Stub for test_remove_config_entry (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_restore_state() -> None:
    """Stub for test_light_restore_state (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_restore_state_bad_cache() -> None:
    """Stub for test_light_restore_state_bad_cache (port deferred)."""


