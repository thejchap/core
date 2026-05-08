"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def async_setup_entry() -> None:
    """Stub for test_async_setup_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_not_ready() -> None:
    """Stub for test_config_not_ready."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def error_on_init() -> None:
    """Stub for test_error_on_init."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def migrate_entry() -> None:
    """Stub for test_migrate_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def serial_mismatch() -> None:
    """Stub for test_serial_mismatch."""

