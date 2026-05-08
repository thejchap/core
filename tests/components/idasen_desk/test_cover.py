"""Tryke skip-stubs for test_cover.py - sibling port deferred (123 LOC, 2 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (123 LOC, 2 parametrize)")
async def cover_available() -> None:
    """Stub for test_cover_available."""

@test.skip("sibling port deferred (123 LOC, 2 parametrize)")
async def cover_services() -> None:
    """Stub for test_cover_services."""

@test.skip("sibling port deferred (123 LOC, 2 parametrize)")
async def cover_services_exception() -> None:
    """Stub for test_cover_services_exception."""
