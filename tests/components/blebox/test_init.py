"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_failure() -> None:
    """Stub for test_setup_failure."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_failure_on_connection() -> None:
    """Stub for test_setup_failure_on_connection."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unload_config_entry() -> None:
    """Stub for test_unload_config_entry."""

