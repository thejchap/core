"""Tryke skip stub for test_init.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("snapshot test — out of scope")
async def async_setup_entry_success() -> None:
    """Stub for test_async_setup_entry_success."""


@test.skip("snapshot test — out of scope")
async def async_setup_entry_device_not_found() -> None:
    """Stub for test_async_setup_entry_device_not_found."""


@test.skip("snapshot test — out of scope")
async def async_unload_entry() -> None:
    """Stub for test_async_unload_entry."""


@test.skip("snapshot test — out of scope")
async def device_info() -> None:
    """Stub for test_device_info."""


@test.skip("snapshot test — out of scope")
async def poll_bleak_error_logs_unavailable() -> None:
    """Stub for test_poll_bleak_error_logs_unavailable."""


@test.skip("snapshot test — out of scope")
async def poll_generic_exception_logs_unavailable() -> None:
    """Stub for test_poll_generic_exception_logs_unavailable."""


@test.skip("snapshot test — out of scope")
async def poll_recovery_logs_back_online() -> None:
    """Stub for test_poll_recovery_logs_back_online."""


