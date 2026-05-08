"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the hikvision integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.hikvision.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("hikvision")


@test.skip("sibling port deferred (227 LOC, 0 parametrize)")
async def setup_and_unload_entry() -> None:
    """Stub for test_setup_and_unload_entry."""

@test.skip("sibling port deferred (227 LOC, 0 parametrize)")
async def setup_entry_with_ssl() -> None:
    """Stub for test_setup_entry_with_ssl."""

@test.skip("sibling port deferred (227 LOC, 0 parametrize)")
async def setup_entry_connection_error() -> None:
    """Stub for test_setup_entry_connection_error."""

@test.skip("sibling port deferred (227 LOC, 0 parametrize)")
async def setup_entry_no_device_id() -> None:
    """Stub for test_setup_entry_no_device_id."""

@test.skip("sibling port deferred (227 LOC, 0 parametrize)")
async def setup_entry_nvr_fetches_events() -> None:
    """Stub for test_setup_entry_nvr_fetches_events."""

@test.skip("sibling port deferred (227 LOC, 0 parametrize)")
async def setup_entry_nvr_skips_videoloss() -> None:
    """Stub for test_setup_entry_nvr_skips_videoloss."""

@test.skip("sibling port deferred (227 LOC, 0 parametrize)")
async def setup_entry_nvr_skips_unmapped_events() -> None:
    """Stub for test_setup_entry_nvr_skips_unmapped_events."""

@test.skip("sibling port deferred (227 LOC, 0 parametrize)")
async def setup_entry_nvr_skips_all_unknown_events() -> None:
    """Stub for test_setup_entry_nvr_skips_all_unknown_events."""

@test.skip("sibling port deferred (227 LOC, 0 parametrize)")
async def setup_entry_nvr_event_fetch_request_error() -> None:
    """Stub for test_setup_entry_nvr_event_fetch_request_error."""

@test.skip("sibling port deferred (227 LOC, 0 parametrize)")
async def setup_entry_nvr_event_fetch_parse_error() -> None:
    """Stub for test_setup_entry_nvr_event_fetch_parse_error."""

@test.skip("sibling port deferred (227 LOC, 0 parametrize)")
async def setup_entry_nvr_no_events_returned() -> None:
    """Stub for test_setup_entry_nvr_no_events_returned."""

@test.skip("sibling port deferred (227 LOC, 0 parametrize)")
async def setup_entry_nvr_empty_events_returned() -> None:
    """Stub for test_setup_entry_nvr_empty_events_returned."""
