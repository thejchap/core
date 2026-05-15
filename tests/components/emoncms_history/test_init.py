"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup_valid_config() -> None:
    """Stub for test_setup_valid_config (port deferred)."""

@test.skip("pending tryke port")
async def setup_missing_config() -> None:
    """Stub for test_setup_missing_config (port deferred)."""

@test.skip("pending tryke port")
async def emoncms_send_data() -> None:
    """Stub for test_emoncms_send_data (port deferred)."""
