"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def load_unload_config_entry() -> None:
    """Stub for test_load_unload_config_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_reauth_at_setup() -> None:
    """Stub for test_config_entry_reauth_at_setup."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_reauth_while_reconnecting() -> None:
    """Stub for test_config_entry_reauth_while_reconnecting."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def disconnect_on_stop() -> None:
    """Stub for test_disconnect_on_stop."""

