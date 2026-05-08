"""Tryke skip-stubs for test_diagnostics.py - indirect parametrize unsupported."""

from tryke import test

@test.skip("indirect parametrize unsupported")
async def diagnostics() -> None:
    """Stub for test_diagnostics."""
