"""Tryke skip-stubs for onedrive_for_business config flow tests.

Original tests use OAuth2 application credentials flow; full port deferred.
"""

from tryke import test

@test.skip("OAuth2 application credentials flow")
async def full_flow() -> None:
    """Stub for test_full_flow (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def full_flow_with_owner_not_found() -> None:
    """Stub for test_full_flow_with_owner_not_found (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def error_during_folder_creation() -> None:
    """Stub for test_error_during_folder_creation (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def flow_errors() -> None:
    """Stub for test_flow_errors (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def already_configured() -> None:
    """Stub for test_already_configured (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def reconfigure_flow() -> None:
    """Stub for test_reconfigure_flow (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def reconfigure_flow_error() -> None:
    """Stub for test_reconfigure_flow_error (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def reconfigure_flow_wrong_drive() -> None:
    """Stub for test_reconfigure_flow_wrong_drive (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def reauth_flow() -> None:
    """Stub for test_reauth_flow (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def reauth_flow_id_changed() -> None:
    """Stub for test_reauth_flow_id_changed (port deferred)."""
