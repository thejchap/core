"""Tryke skip-stubs for test_services.py - sibling port deferred (300 LOC, 1 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (300 LOC, 1 parametrize)")
async def send() -> None:
    """Stub for test_send."""

@test.skip("sibling port deferred (300 LOC, 1 parametrize)")
async def read() -> None:
    """Stub for test_read."""

@test.skip("sibling port deferred (300 LOC, 1 parametrize)")
async def event_register() -> None:
    """Stub for test_event_register."""

@test.skip("sibling port deferred (300 LOC, 1 parametrize)")
async def exposure_register() -> None:
    """Stub for test_exposure_register."""

@test.skip("sibling port deferred (300 LOC, 1 parametrize)")
async def reload_service() -> None:
    """Stub for test_reload_service."""

@test.skip("sibling port deferred (300 LOC, 1 parametrize)")
async def service_setup_failed() -> None:
    """Stub for test_service_setup_failed."""
