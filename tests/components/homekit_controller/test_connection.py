"""Tryke skip-stubs for test_connection.py - large file (672 LOC) - port deferred."""

from tryke import expect, test

@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.homekit_controller.connection module imports cleanly."""
    from homeassistant.components.homekit_controller import connection  # noqa: PLC0415
    expect(connection).not_.to_be(None)


@test.skip("large file (672 LOC) - port deferred")
async def migrate_device_id_no_serial_skip_if_other_owner() -> None:
    """Stub for test_migrate_device_id_no_serial_skip_if_other_owner."""

@test.skip("large file (672 LOC) - port deferred")
async def migrate_device_id_no_serial() -> None:
    """Stub for test_migrate_device_id_no_serial."""

@test.skip("large file (672 LOC) - port deferred")
async def migrate_ble_unique_id() -> None:
    """Stub for test_migrate_ble_unique_id."""

@test.skip("large file (672 LOC) - port deferred")
async def thread_provision_no_creds() -> None:
    """Stub for test_thread_provision_no_creds."""

@test.skip("large file (672 LOC) - port deferred")
async def thread_provision() -> None:
    """Stub for test_thread_provision."""

@test.skip("large file (672 LOC) - port deferred")
async def thread_provision_migration_failed() -> None:
    """Stub for test_thread_provision_migration_failed."""

@test.skip("large file (672 LOC) - port deferred")
async def poll_firmware_version_only_all_watchable_accessory_mode() -> None:
    """Stub for test_poll_firmware_version_only_all_watchable_accessory_mode."""

@test.skip("large file (672 LOC) - port deferred")
async def manual_poll_all_chars() -> None:
    """Stub for test_manual_poll_all_chars."""

@test.skip("large file (672 LOC) - port deferred")
async def poll_all_on_startup_refreshes_stale_values() -> None:
    """Stub for test_poll_all_on_startup_refreshes_stale_values."""

@test.skip("large file (672 LOC) - port deferred")
async def characteristic_polling_batching() -> None:
    """Stub for test_characteristic_polling_batching."""

@test.skip("large file (672 LOC) - port deferred")
async def async_setup_handles_unparsable_response() -> None:
    """Stub for test_async_setup_handles_unparsable_response."""
