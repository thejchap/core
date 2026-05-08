"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def async_setup_raises_entry_not_ready() -> None:
    """Stub for test_async_setup_raises_entry_not_ready."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def async_setup_raises_entry_auth_failed() -> None:
    """Stub for test_async_setup_raises_entry_auth_failed."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def integration_services() -> None:
    """Stub for test_integration_services."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def integration_services_with_issue() -> None:
    """Stub for test_integration_services_with_issue."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def integration_services_with_nonexisting_record() -> None:
    """Stub for test_integration_services_with_nonexisting_record."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def integration_update_interval() -> None:
    """Stub for test_integration_update_interval."""

