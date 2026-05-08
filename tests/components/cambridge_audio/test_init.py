"""Tryke skip stub for test_init.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def device_info() -> None:
    """Stub for test_device_info."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def disconnect_reconnect_log() -> None:
    """Stub for test_disconnect_reconnect_log."""


