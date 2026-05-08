"""Tryke skip-stubs for onedrive_for_business diagnostics tests.

Original tests use OAuth2 application credentials flow + onedrive_personal_sdk mocks; full port deferred.
"""

from tryke import test

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def diagnostics() -> None:
    """Test diagnostics."""
