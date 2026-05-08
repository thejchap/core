"""Tryke skip-stubs for test_init.py - sibling port deferred (225 LOC, 3 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (225 LOC, 3 parametrize)")
async def setup_platforms() -> None:
    """Stub for test_setup_platforms."""

@test.skip("sibling port deferred (225 LOC, 3 parametrize)")
async def stale_devices_cleanup() -> None:
    """Stub for test_stale_devices_cleanup."""

@test.skip("sibling port deferred (225 LOC, 3 parametrize)")
async def coordinator_updates() -> None:
    """Stub for test_coordinator_updates."""

@test.skip("sibling port deferred (225 LOC, 3 parametrize)")
async def coordinator_update_fails() -> None:
    """Stub for test_coordinator_update_fails."""

@test.skip("sibling port deferred (225 LOC, 3 parametrize)")
async def entry_setup_fails() -> None:
    """Stub for test_entry_setup_fails."""
