"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def load_unload_entry() -> None:
    """Stub for test_load_unload_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def load_withoutbrand() -> None:
    """Stub for test_load_withoutbrand."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def coordinator_update_valid_refresh_token() -> None:
    """Stub for test_coordinator_update_valid_refresh_token."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def coordinator_update_expired_refresh_token() -> None:
    """Stub for test_coordinator_update_expired_refresh_token."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def load_exceptions() -> None:
    """Stub for test_load_exceptions."""

