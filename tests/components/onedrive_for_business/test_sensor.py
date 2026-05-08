"""Tryke skip-stubs for onedrive_for_business sensor tests.

Original tests use OAuth2 application credentials flow + onedrive_personal_sdk mocks; full port deferred.
"""

from tryke import test

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def sensors() -> None:
    """Test the OneDrive for Business sensors."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def update_failure() -> None:
    """Ensure sensors are going unavailable on update failure."""
