"""Tryke skip stub for test_init.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def async_setup_entry() -> None:
    """Stub for test_async_setup_entry."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def connection_error() -> None:
    """Stub for test_connection_error."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def unload_remove_entry() -> None:
    """Stub for test_unload_remove_entry."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def availability() -> None:
    """Stub for test_availability."""


