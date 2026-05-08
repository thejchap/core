"""Tryke skip-stubs for test_backup.py - indirect parametrize unsupported."""

from tryke import test

@test.skip("indirect parametrize unsupported")
async def suggested_filenames() -> None:
    """Stub for test_suggested_filenames."""

@test.skip("indirect parametrize unsupported")
async def agents_info() -> None:
    """Stub for test_agents_info."""

@test.skip("indirect parametrize unsupported")
async def agents_list_backups() -> None:
    """Stub for test_agents_list_backups."""

@test.skip("indirect parametrize unsupported")
async def agents_get_backup() -> None:
    """Stub for test_agents_get_backup."""

@test.skip("indirect parametrize unsupported")
async def agents_get_backup_does_not_throw_on_not_found() -> None:
    """Stub for test_agents_get_backup_does_not_throw_on_not_found."""

@test.skip("indirect parametrize unsupported")
async def agents_list_backups_with_corrupted_metadata() -> None:
    """Stub for test_agents_list_backups_with_corrupted_metadata."""

@test.skip("indirect parametrize unsupported")
async def agents_delete() -> None:
    """Stub for test_agents_delete."""

@test.skip("indirect parametrize unsupported")
async def agents_delete_not_throwing_on_not_found() -> None:
    """Stub for test_agents_delete_not_throwing_on_not_found."""

@test.skip("indirect parametrize unsupported")
async def agents_upload() -> None:
    """Stub for test_agents_upload."""

@test.skip("indirect parametrize unsupported")
async def agents_upload_network_failure() -> None:
    """Stub for test_agents_upload_network_failure."""

@test.skip("indirect parametrize unsupported")
async def multipart_upload_consistent_part_sizes() -> None:
    """Stub for test_multipart_upload_consistent_part_sizes."""

@test.skip("indirect parametrize unsupported")
async def agents_upload_on_progress() -> None:
    """Stub for test_agents_upload_on_progress."""

@test.skip("indirect parametrize unsupported")
async def agents_download() -> None:
    """Stub for test_agents_download."""

@test.skip("indirect parametrize unsupported")
async def error_during_delete() -> None:
    """Stub for test_error_during_delete."""

@test.skip("indirect parametrize unsupported")
async def cache_expiration() -> None:
    """Stub for test_cache_expiration."""

@test.skip("indirect parametrize unsupported")
async def listeners_get_cleaned_up() -> None:
    """Stub for test_listeners_get_cleaned_up."""

@test.skip("indirect parametrize unsupported")
async def list_backups_with_pagination() -> None:
    """Stub for test_list_backups_with_pagination."""
