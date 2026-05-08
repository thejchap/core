"""Tryke skip-stubs for test_diagnostics.py - recorder_mock fixture coupling."""

from tryke import test

@test.skip("recorder_mock fixture coupling")
async def diagnostics() -> None:
    """Stub for test_diagnostics."""
