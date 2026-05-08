"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_setup() -> None:
    """Stub for test_config_setup."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_not_ready() -> None:
    """Stub for test_config_not_ready."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def reload_config_entry() -> None:
    """Stub for test_reload_config_entry."""

