"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def duplicate_removal() -> None:
    """Stub for test_duplicate_removal."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unique_id_migrate() -> None:
    """Stub for test_unique_id_migrate."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def client_update_connection_error() -> None:
    """Stub for test_client_update_connection_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def client_connection_error() -> None:
    """Stub for test_client_connection_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def timeout_error() -> None:
    """Stub for test_timeout_error."""

