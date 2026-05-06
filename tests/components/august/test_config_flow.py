"""Tryke skip-stubs for august config flow tests.

Original tests use OAuth2 application credentials flow; full port deferred.
"""

from tryke import test

@test.skip("OAuth2 application credentials flow")
async def full_flow() -> None:
    """Stub for test_full_flow (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def full_flow_already_exists() -> None:
    """Stub for test_full_flow_already_exists (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def reauth() -> None:
    """Stub for test_reauth (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def reauth_wrong_account() -> None:
    """Stub for test_reauth_wrong_account (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def legacy_migration_with_email_match() -> None:
    """Stub for test_legacy_migration_with_email_match (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def legacy_migration_wrong_email() -> None:
    """Stub for test_legacy_migration_wrong_email (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def legacy_migration_no_email_in_jwt() -> None:
    """Stub for test_legacy_migration_no_email_in_jwt (port deferred)."""
