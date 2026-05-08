"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def import() -> None:
    """Stub for test_import."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def filter_only_config() -> None:
    """Stub for test_filter_only_config."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def failed_test_connection() -> None:
    """Stub for test_failed_test_connection."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def send_batch_error() -> None:
    """Stub for test_send_batch_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def late_event() -> None:
    """Stub for test_late_event."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def full_batch() -> None:
    """Stub for test_full_batch."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def filter() -> None:
    """Stub for test_filter."""

