"""Tryke skip-stubs for test_events.py - sibling port deferred (152 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (152 LOC, 0 parametrize)")
async def fire_transponder_event() -> None:
    """Stub for test_fire_transponder_event."""

@test.skip("sibling port deferred (152 LOC, 0 parametrize)")
async def fire_fingerprint_event() -> None:
    """Stub for test_fire_fingerprint_event."""

@test.skip("sibling port deferred (152 LOC, 0 parametrize)")
async def fire_codelock_event() -> None:
    """Stub for test_fire_codelock_event."""

@test.skip("sibling port deferred (152 LOC, 0 parametrize)")
async def fire_transmitter_event() -> None:
    """Stub for test_fire_transmitter_event."""

@test.skip("sibling port deferred (152 LOC, 0 parametrize)")
async def fire_sendkeys_event() -> None:
    """Stub for test_fire_sendkeys_event."""

@test.skip("sibling port deferred (152 LOC, 0 parametrize)")
async def dont_fire_on_non_module_input() -> None:
    """Stub for test_dont_fire_on_non_module_input."""
