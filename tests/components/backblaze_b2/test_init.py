"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def load_unload_config_entry() -> None:
    """Stub for test_load_unload_config_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_entry_invalid_auth() -> None:
    """Stub for test_setup_entry_invalid_auth."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_entry_restricted_bucket() -> None:
    """Stub for test_setup_entry_restricted_bucket."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def periodic_issue_check() -> None:
    """Stub for test_periodic_issue_check."""

