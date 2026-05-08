"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_setup() -> None:
    """Stub for test_config_entry_setup."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_setup_relative_directory() -> None:
    """Stub for test_config_entry_setup_relative_directory."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_setup_not_existing_directory() -> None:
    """Stub for test_config_entry_setup_not_existing_directory."""

