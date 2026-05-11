"""Tryke skip-stubs for test_init.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot test — out of scope")
async def setup() -> None:
    """Stub for test_setup."""

@test.skip("snapshot test — out of scope")
async def setup_missing_pin() -> None:
    """Stub for test_setup_missing_pin."""

@test.skip("snapshot test — out of scope")
async def setup_failed_connect() -> None:
    """Stub for test_setup_failed_connect."""

@test.skip("snapshot test — out of scope")
async def setup_unknown_error() -> None:
    """Stub for test_setup_unknown_error."""

@test.skip("snapshot test — out of scope")
async def setup_invalid_pin() -> None:
    """Stub for test_setup_invalid_pin."""
