"""Tryke skip-stubs for test_init.py - sibling port deferred (64 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (64 LOC, 0 parametrize)")
async def setup() -> None:
    """Stub for test_setup."""

@test.skip("sibling port deferred (64 LOC, 0 parametrize)")
async def async_setup_entry_not_ready() -> None:
    """Stub for test_async_setup_entry_not_ready."""

@test.skip("sibling port deferred (64 LOC, 0 parametrize)")
async def async_setup_entry_auth_failed() -> None:
    """Stub for test_async_setup_entry_auth_failed."""

@test.skip("sibling port deferred (64 LOC, 0 parametrize)")
async def device_info() -> None:
    """Stub for test_device_info."""
