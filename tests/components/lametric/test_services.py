"""Tryke skip-stubs for test_services.py - sibling port deferred (210 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (210 LOC, 0 parametrize)")
async def service_chart() -> None:
    """Stub for test_service_chart."""

@test.skip("sibling port deferred (210 LOC, 0 parametrize)")
async def service_message() -> None:
    """Stub for test_service_message."""
