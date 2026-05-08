"""Tryke skip-stubs for onedrive_for_business backup tests.

Original tests use OAuth2 application credentials flow + onedrive_personal_sdk mocks; full port deferred.
"""

from tryke import test

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def agents_info() -> None:
    """Test backup agent info."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def agents_list_backups() -> None:
    """Test agent list backups."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def agents_list_backups_with_download_failure() -> None:
    """Test agent list backups still works if one of the items fails to download."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def agents_get_backup() -> None:
    """Test agent get backup."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def agents_get_backup_missing_file() -> None:
    """Test what happens when only metadata exists."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def agents_delete() -> None:
    """Test agent delete backup."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def agents_upload() -> None:
    """Test agent upload backup."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def agents_upload_corrupt_upload() -> None:
    """Test hash validation fails."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def agents_upload_metadata_upload_failed() -> None:
    """Test metadata upload fails."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def agents_download() -> None:
    """Test agent download backup."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def error_on_agents_download() -> None:
    """Test we get not found on an not existing backup on download."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def delete_error() -> None:
    """Test error during delete."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def agents_delete_not_found_does_not_throw() -> None:
    """Test agent delete backup."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def agents_backup_not_found() -> None:
    """Test backup not found."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def reauth_on_403() -> None:
    """Test we re-authenticate on 403."""

@test.skip("OAuth2 application credentials flow + onedrive_personal_sdk mocks")
async def listeners_get_cleaned_up() -> None:
    """Test listener gets cleaned up."""
