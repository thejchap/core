"""Tryke skip-stubs for test_system_health.py - sibling port deferred (102 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (102 LOC, 0 parametrize)")
async def system_health() -> None:
    """Stub for test_system_health."""

@test.skip("sibling port deferred (102 LOC, 0 parametrize)")
async def system_health_failed_connect() -> None:
    """Stub for test_system_health_failed_connect."""
