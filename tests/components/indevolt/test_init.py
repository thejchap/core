"""Tryke skip-stubs for test_init.py - indirect parametrize unsupported."""

from tryke import test

@test.skip("indirect parametrize unsupported")
async def load_unload() -> None:
    """Stub for test_load_unload."""

@test.skip("indirect parametrize unsupported")
async def load_failure() -> None:
    """Stub for test_load_failure."""
