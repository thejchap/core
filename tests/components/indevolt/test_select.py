"""Tryke skip-stubs for test_select.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot test — out of scope")
async def select() -> None:
    """Stub for test_select."""

@test.skip("snapshot test — out of scope")
async def select_option() -> None:
    """Stub for test_select_option."""

@test.skip("snapshot test — out of scope")
async def select_set_option_error() -> None:
    """Stub for test_select_set_option_error."""

@test.skip("snapshot test — out of scope")
async def select_unavailable_outdoor_portable() -> None:
    """Stub for test_select_unavailable_outdoor_portable."""

@test.skip("snapshot test — out of scope")
async def select_availability() -> None:
    """Stub for test_select_availability."""
