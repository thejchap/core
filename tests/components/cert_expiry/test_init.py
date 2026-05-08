"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update_unique_id() -> None:
    """Stub for test_update_unique_id."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unload_config_entry() -> None:
    """Stub for test_unload_config_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def delay_load_during_startup() -> None:
    """Stub for test_delay_load_during_startup."""

