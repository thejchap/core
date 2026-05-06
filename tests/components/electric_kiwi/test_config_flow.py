"""Tryke skip-stubs for electric_kiwi config flow tests.

Original tests use OAuth2 application credentials flow; full port deferred.
"""

from tryke import test

@test.skip("OAuth2 application credentials flow")
async def full_flow() -> None:
    """Stub for test_full_flow (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def flow_failure() -> None:
    """Stub for test_flow_failure (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def existing_entry() -> None:
    """Stub for test_existing_entry (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def reauthentication() -> None:
    """Stub for test_reauthentication (port deferred)."""
