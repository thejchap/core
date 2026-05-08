"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def async_setup_entry_not_ready() -> None:
    """Stub for test_async_setup_entry_not_ready."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update_failed() -> None:
    """Stub for test_update_failed."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def device_info() -> None:
    """Stub for test_device_info."""

