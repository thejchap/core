"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def load_unload_config_entry() -> None:
    """Stub for test_load_unload_config_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_entry_create_client_errors() -> None:
    """Stub for test_setup_entry_create_client_errors."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_entry_head_bucket_error() -> None:
    """Stub for test_setup_entry_head_bucket_error."""

