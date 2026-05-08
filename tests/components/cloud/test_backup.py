"""Tryke skip stub for test_backup.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_info() -> None:
    """Stub for test_agents_info."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_list_backups() -> None:
    """Stub for test_agents_list_backups."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_list_backups_fail_cloud() -> None:
    """Stub for test_agents_list_backups_fail_cloud."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_get_backup() -> None:
    """Stub for test_agents_get_backup."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_download() -> None:
    """Stub for test_agents_download."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_download_fail_get() -> None:
    """Stub for test_agents_download_fail_get."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_download_not_found() -> None:
    """Stub for test_agents_download_not_found."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_upload() -> None:
    """Stub for test_agents_upload."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_upload_on_progress() -> None:
    """Stub for test_agents_upload_on_progress."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_upload_fail() -> None:
    """Stub for test_agents_upload_fail."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_upload_fail_non_retryable() -> None:
    """Stub for test_agents_upload_fail_non_retryable."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_upload_not_protected() -> None:
    """Stub for test_agents_upload_not_protected."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_upload_not_subscribed() -> None:
    """Stub for test_agents_upload_not_subscribed."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_upload_not_subscribed_midway() -> None:
    """Stub for test_agents_upload_not_subscribed_midway."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_upload_wrong_size() -> None:
    """Stub for test_agents_upload_wrong_size."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_delete() -> None:
    """Stub for test_agents_delete."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_delete_fail_cloud() -> None:
    """Stub for test_agents_delete_fail_cloud."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_delete_not_found() -> None:
    """Stub for test_agents_delete_not_found."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def calling_listener_on_login_logout() -> None:
    """Stub for test_calling_listener_on_login_logout."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def not_calling_listener_after_unsub() -> None:
    """Stub for test_not_calling_listener_after_unsub."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def not_calling_listener_with_unknown_event_type() -> None:
    """Stub for test_not_calling_listener_with_unknown_event_type."""

