"""Tryke skip-stubs for netatmo config flow tests.

Original tests use OAuth2 application credentials flow; full port deferred.
"""

from tryke import test

@test.skip("OAuth2 application credentials flow")
async def abort_if_existing_entry() -> None:
    """Stub for test_abort_if_existing_entry (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def full_flow() -> None:
    """Stub for test_full_flow (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def option_flow() -> None:
    """Stub for test_option_flow (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def option_flow_wrong_coordinates() -> None:
    """Stub for test_option_flow_wrong_coordinates (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def reauth() -> None:
    """Stub for test_reauth (port deferred)."""
