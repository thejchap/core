"""Tryke skip stubs for test_panel - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def get_config() -> None:
    """Stub for test_get_config (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def save_config() -> None:
    """Stub for test_save_config (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def save_config_invalid_entry() -> None:
    """Stub for test_save_config_invalid_entry (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def panel_registration() -> None:
    """Stub for test_panel_registration (port deferred)."""


