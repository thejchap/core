"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def load_unload_entry() -> None:
    """Stub for test_load_unload_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def auth_failed() -> None:
    """Stub for test_auth_failed."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update_failed_project() -> None:
    """Stub for test_update_failed_project."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update_failed_builds() -> None:
    """Stub for test_update_failed_builds."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def no_builds() -> None:
    """Stub for test_no_builds."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def no_work_item_types() -> None:
    """Stub for test_no_work_item_types."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def no_work_item_ids() -> None:
    """Stub for test_no_work_item_ids."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def no_work_items() -> None:
    """Stub for test_no_work_items."""

