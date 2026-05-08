"""Tryke skip stub for test_backup.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the google_drive.backup module imports cleanly."""
    from homeassistant.components.google_drive import backup  # noqa: PLC0415
    expect(backup).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def agents_info() -> None:
    """Stub for test_agents_info."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def agents_list_backups() -> None:
    """Stub for test_agents_list_backups."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def agents_list_backups_fail() -> None:
    """Stub for test_agents_list_backups_fail."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def agents_get_backup() -> None:
    """Stub for test_agents_get_backup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def agents_download() -> None:
    """Stub for test_agents_download."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def agents_download_fail() -> None:
    """Stub for test_agents_download_fail."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def agents_download_file_not_found() -> None:
    """Stub for test_agents_download_file_not_found."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def agents_download_metadata_not_found() -> None:
    """Stub for test_agents_download_metadata_not_found."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def agents_upload() -> None:
    """Stub for test_agents_upload."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def agents_upload_create_folder_if_missing() -> None:
    """Stub for test_agents_upload_create_folder_if_missing."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def agents_upload_progress() -> None:
    """Stub for test_agents_upload_progress."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def agents_upload_fail() -> None:
    """Stub for test_agents_upload_fail."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def agents_delete() -> None:
    """Stub for test_agents_delete."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def agents_delete_fail() -> None:
    """Stub for test_agents_delete_fail."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def agents_delete_not_found() -> None:
    """Stub for test_agents_delete_not_found."""

