"""Tryke skip-stubs for test_diagnostics.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def diagnostics() -> None:
    """Stub for test_diagnostics."""
