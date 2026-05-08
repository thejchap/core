"""Tryke skip-stubs for test_entity_availability.py - sibling port deferred (66 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (66 LOC, 0 parametrize)")
async def controller_offline() -> None:
    """Stub for test_controller_offline."""

@test.skip("sibling port deferred (66 LOC, 0 parametrize)")
async def api_offline() -> None:
    """Stub for test_api_offline."""
