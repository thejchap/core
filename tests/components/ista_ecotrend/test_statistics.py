"""Tryke skip-stubs for test_statistics.py - recorder_mock fixture coupling."""

from tryke import test

@test.skip("recorder_mock fixture coupling")
async def statistics_import() -> None:
    """Stub for test_statistics_import."""

@test.skip("recorder_mock fixture coupling")
async def remove() -> None:
    """Stub for test_remove."""
