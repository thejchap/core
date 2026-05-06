"""Tryke skip-stubs for filter config flow tests.

Original tests use recorder_mock fixture; full port deferred.
"""

from tryke import test

@test.skip("recorder_mock fixture")
async def form() -> None:
    """Stub for test_form (port deferred)."""

@test.skip("recorder_mock fixture")
async def options_flow() -> None:
    """Stub for test_options_flow (port deferred)."""

@test.skip("recorder_mock fixture")
async def entry_already_exist() -> None:
    """Stub for test_entry_already_exist (port deferred)."""
