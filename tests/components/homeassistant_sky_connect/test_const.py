"""Tryke skip-stubs for test_const.py - sibling port deferred (27 LOC, 1 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (27 LOC, 1 parametrize)")
async def hardware_variant() -> None:
    """Stub for test_hardware_variant."""

@test.skip("sibling port deferred (27 LOC, 1 parametrize)")
async def hardware_variant_invalid() -> None:
    """Stub for test_hardware_variant_invalid."""
