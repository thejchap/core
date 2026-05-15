"""Tryke skip stub (requires unported fixture)."""

from tryke import test


@test.skip("requires recorder_mock (not in tryke shim)")
async def async_pre_backup() -> None:
    """Stub for test_async_pre_backup (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def async_pre_backup_core_state() -> None:
    """Stub for test_async_pre_backup_core_state (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def async_pre_backup_with_timeout() -> None:
    """Stub for test_async_pre_backup_with_timeout (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def async_pre_backup_with_migration() -> None:
    """Stub for test_async_pre_backup_with_migration (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def async_post_backup() -> None:
    """Stub for test_async_post_backup (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def async_post_backup_failure() -> None:
    """Stub for test_async_post_backup_failure (port deferred)."""
