"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def using_file() -> None:
    """Stub for test_using_file (port deferred)."""

@test.skip("pending tryke port")
async def removing_file() -> None:
    """Stub for test_removing_file (port deferred)."""

@test.skip("pending tryke port")
async def removed_on_stop() -> None:
    """Stub for test_removed_on_stop (port deferred)."""

@test.skip("pending tryke port")
async def upload_large_file() -> None:
    """Stub for test_upload_large_file (port deferred)."""

@test.skip("pending tryke port")
async def upload_with_wrong_key_fails() -> None:
    """Stub for test_upload_with_wrong_key_fails (port deferred)."""

@test.skip("pending tryke port")
async def upload_large_file_fails() -> None:
    """Stub for test_upload_large_file_fails (port deferred)."""
