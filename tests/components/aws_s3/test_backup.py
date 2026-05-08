"""Tryke skip stub for test_backup.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def suggested_filenames() -> None:
    """Stub for test_suggested_filenames."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_info() -> None:
    """Stub for test_agents_info."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_list_backups() -> None:
    """Stub for test_agents_list_backups."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_get_backup() -> None:
    """Stub for test_agents_get_backup."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_get_backup_does_not_throw_on_not_found() -> None:
    """Stub for test_agents_get_backup_does_not_throw_on_not_found."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_list_backups_with_corrupted_metadata() -> None:
    """Stub for test_agents_list_backups_with_corrupted_metadata."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_delete() -> None:
    """Stub for test_agents_delete."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_delete_not_throwing_on_not_found() -> None:
    """Stub for test_agents_delete_not_throwing_on_not_found."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_upload_network_failure() -> None:
    """Stub for test_agents_upload_network_failure."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_upload_on_progress() -> None:
    """Stub for test_agents_upload_on_progress."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_download() -> None:
    """Stub for test_agents_download."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def error_during_delete() -> None:
    """Stub for test_error_during_delete."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def cache_expiration() -> None:
    """Stub for test_cache_expiration."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def listeners_get_cleaned_up() -> None:
    """Stub for test_listeners_get_cleaned_up."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def list_backups_with_pagination() -> None:
    """Stub for test_list_backups_with_pagination."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agent_list_backups_parametrized() -> None:
    """Stub for test_agent_list_backups_parametrized."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agent_delete_backup_parametrized() -> None:
    """Stub for test_agent_delete_backup_parametrized."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agent_upload_small_backup_parametrized() -> None:
    """Stub for test_agent_upload_small_backup_parametrized."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agent_upload_large_backup_parametrized() -> None:
    """Stub for test_agent_upload_large_backup_parametrized."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agent_download_backup_parametrized() -> None:
    """Stub for test_agent_download_backup_parametrized."""

