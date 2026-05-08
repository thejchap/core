"""Tryke skip-stubs for overkiz init tests.

Original tests use OverkizClient API mocks + token refresh; full port deferred.
"""

from tryke import test

@test.skip("OverkizClient API mocks + token refresh")
async def unique_id_migration() -> None:
    """Test migration of sensor unique IDs."""
