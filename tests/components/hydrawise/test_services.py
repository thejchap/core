"""Tryke skip-stubs for test_services.py - sibling port deferred (93 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (93 LOC, 0 parametrize)")
async def start_watering() -> None:
    """Stub for test_start_watering."""

@test.skip("sibling port deferred (93 LOC, 0 parametrize)")
async def start_watering_no_duration() -> None:
    """Stub for test_start_watering_no_duration."""

@test.skip("sibling port deferred (93 LOC, 0 parametrize)")
async def resume() -> None:
    """Stub for test_resume."""

@test.skip("sibling port deferred (93 LOC, 0 parametrize)")
async def suspend() -> None:
    """Stub for test_suspend."""
