"""Tryke skip stub for test_init.py."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.azure_data_explorer module imports cleanly."""
    from homeassistant.components import azure_data_explorer  # noqa: PLC0415
    expect(azure_data_explorer).not_.to_be(None)


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def put_event_on_queue_with_managed_client() -> None:
    """Stub for test_put_event_on_queue_with_managed_client."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def put_event_on_queue_with_managed_client_with_errors() -> None:
    """Stub for test_put_event_on_queue_with_managed_client_with_errors."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def put_event_on_queue_with_queueing_client() -> None:
    """Stub for test_put_event_on_queue_with_queueing_client."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def late_event() -> None:
    """Stub for test_late_event."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def filter() -> None:
    """Stub for test_filter."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def event() -> None:
    """Stub for test_event."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def connection() -> None:
    """Stub for test_connection."""

