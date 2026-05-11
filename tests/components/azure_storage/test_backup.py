"""Tryke skip stub for test_backup.py."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.azure_storage.backup module imports cleanly."""
    from homeassistant.components.azure_storage import backup  # noqa: PLC0415
    expect(backup).not_.to_be(None)


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
async def agents_delete() -> None:
    """Stub for test_agents_delete."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_delete_not_throwing_on_not_found() -> None:
    """Stub for test_agents_delete_not_throwing_on_not_found."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_upload() -> None:
    """Stub for test_agents_upload."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_download() -> None:
    """Stub for test_agents_download."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def agents_error_on_download_not_found() -> None:
    """Stub for test_agents_error_on_download_not_found."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def error_during_delete() -> None:
    """Stub for test_error_during_delete."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def listeners_get_cleaned_up() -> None:
    """Stub for test_listeners_get_cleaned_up."""

