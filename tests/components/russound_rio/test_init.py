"""Tests for the Russound RIO integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready (port deferred)."""

@test.skip("syrupy snapshot")
async def device_info() -> None:
    """Stub for test_device_info (port deferred)."""

@test.skip("syrupy snapshot")
async def disconnect_reconnect_log() -> None:
    """Stub for test_disconnect_reconnect_log (port deferred)."""

@test.skip("syrupy snapshot")
async def migrate_entry_from_v1_to_v2_on_setup() -> None:
    """Stub for test_migrate_entry_from_v1_to_v2_on_setup (port deferred)."""

@test.skip("syrupy snapshot")
async def migrate_entry_from_future_version_fails_on_setup() -> None:
    """Stub for test_migrate_entry_from_future_version_fails_on_setup (port deferred)."""

@test.skip("syrupy snapshot")
async def setup_entry_uses_tcp_handler() -> None:
    """Stub for test_setup_entry_uses_tcp_handler (port deferred)."""

@test.skip("syrupy snapshot")
async def setup_entry_uses_serial_handler() -> None:
    """Stub for test_setup_entry_uses_serial_handler (port deferred)."""
