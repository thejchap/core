"""Tryke skip-stubs for test_services.py - indirect parametrize unsupported."""

from tryke import test

@test.skip("indirect parametrize unsupported")
async def get_omer_blessing() -> None:
    """Stub for test_get_omer_blessing."""
