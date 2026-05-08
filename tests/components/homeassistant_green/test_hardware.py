"""Tryke skip-stubs for test_hardware.py - sibling port deferred (101 LOC, 1 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (101 LOC, 1 parametrize)")
async def hardware_info() -> None:
    """Stub for test_hardware_info."""

@test.skip("sibling port deferred (101 LOC, 1 parametrize)")
async def hardware_info_fail() -> None:
    """Stub for test_hardware_info_fail."""
