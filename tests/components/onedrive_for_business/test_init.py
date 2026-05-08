"""Tryke skip-stubs for onedrive_for_business init tests.

Original tests use OAuth2 application credentials flow + onedrive_personal_sdk mocks; full port deferred.
"""

from tryke import test

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def load_unload_config_entry() -> None:
    """Test loading and unloading the integration."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def approot_errors() -> None:
    """Test errors during approot retrieval."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def get_integration_folder_creation() -> None:
    """Test faulty integration folder creation."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def get_integration_folder_creation_error() -> None:
    """Test faulty integration folder creation error."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def oauth_implementation_not_available() -> None:
    """Test that unavailable OAuth implementation raises ConfigEntryNotReady."""
