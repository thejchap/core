"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup_entry() -> None:
    """Stub for test_setup_entry (port deferred)."""

@test.skip("pending tryke port")
async def setup_entry_with_tracing() -> None:
    """Stub for test_setup_entry_with_tracing (port deferred)."""

@test.skip("pending tryke port")
async def process_before_send() -> None:
    """Stub for test_process_before_send (port deferred)."""

@test.skip("pending tryke port")
async def event_with_platform_context() -> None:
    """Stub for test_event_with_platform_context (port deferred)."""

@test.skip("pending tryke port")
async def logger_event_extraction() -> None:
    """Stub for test_logger_event_extraction (port deferred)."""

@test.skip("pending tryke port")
async def filter_log_events() -> None:
    """Stub for test_filter_log_events (port deferred)."""

@test.skip("pending tryke port")
async def filter_handled_events() -> None:
    """Stub for test_filter_handled_events (port deferred)."""
