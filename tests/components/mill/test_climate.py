"""Tryke skip-stubs for mill climate tests."""

from tryke import test


@test.skip("recorder_mock — needs setup_recorder_mock helper integration")
async def climate_placeholder() -> None:
    """Placeholder skipped sibling tests for test_climate.py."""
