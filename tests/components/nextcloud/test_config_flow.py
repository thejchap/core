"""Tryke skip-stubs for nextcloud config flow tests.

Original tests use syrupy snapshot fixture; full port deferred.
"""

from tryke import test

@test.skip("syrupy snapshot fixture")
async def user_create_entry() -> None:
    """Stub for test_user_create_entry (port deferred)."""

@test.skip("syrupy snapshot fixture")
async def user_already_configured() -> None:
    """Stub for test_user_already_configured (port deferred)."""

@test.skip("syrupy snapshot fixture")
async def reauth() -> None:
    """Stub for test_reauth (port deferred)."""
