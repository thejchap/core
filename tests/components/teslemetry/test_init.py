"""Tryke skip-stubs for teslemetry/test_init.py."""

from tryke import test


@test.skip("requires teslemetry API + snapshot — port deferred")
async def load_unload() -> None:
    """Stub for test_load_unload."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def init_error() -> None:
    """Stub for test_init_error."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def devices() -> None:
    """Stub for test_devices."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def vehicle_refresh_error() -> None:
    """Stub for test_vehicle_refresh_error."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def energy_live_refresh_error() -> None:
    """Stub for test_energy_live_refresh_error."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def energy_site_refresh_error() -> None:
    """Stub for test_energy_site_refresh_error."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def vehicle_stream() -> None:
    """Stub for test_vehicle_stream."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def no_live_status() -> None:
    """Stub for test_no_live_status."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def modern_no_poll() -> None:
    """Stub for test_modern_no_poll."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def stale_device_removal() -> None:
    """Stub for test_stale_device_removal."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def skipped_energy_site_is_removed_as_stale_device() -> None:
    """Stub for test_skipped_energy_site_is_removed_as_stale_device."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def device_retention_during_reload() -> None:
    """Stub for test_device_retention_during_reload."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def migrate_from_version_1_success() -> None:
    """Stub for test_migrate_from_version_1_success."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def migrate_from_version_1_token_endpoint_error() -> None:
    """Stub for test_migrate_from_version_1_token_endpoint_error."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def migrate_version_2_no_migration_needed() -> None:
    """Stub for test_migrate_version_2_no_migration_needed."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def migrate_from_future_version_fails() -> None:
    """Stub for test_migrate_from_future_version_fails."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def oauth_implementation_not_available() -> None:
    """Stub for test_oauth_implementation_not_available."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def site_info_retry_exceptions() -> None:
    """Stub for test_site_info_retry_exceptions."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def vehicle_data_retry_exceptions() -> None:
    """Stub for test_vehicle_data_retry_exceptions."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def live_status_coordinator_retry_exceptions() -> None:
    """Stub for test_live_status_coordinator_retry_exceptions."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def energy_history_coordinator_retry_exceptions() -> None:
    """Stub for test_energy_history_coordinator_retry_exceptions."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def live_status_auth_error() -> None:
    """Stub for test_live_status_auth_error."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def live_status_generic_error() -> None:
    """Stub for test_live_status_generic_error."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def missing_token_data() -> None:
    """Stub for test_missing_token_data."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def vehicle_streaming_version_update() -> None:
    """Stub for test_vehicle_streaming_version_update."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def vehicle_streaming_version_update_ignores_none() -> None:
    """Stub for test_vehicle_streaming_version_update_ignores_none."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def vehicle_polling_version_update() -> None:
    """Stub for test_vehicle_polling_version_update."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def energy_site_version_update() -> None:
    """Stub for test_energy_site_version_update."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def live_status_auth_failed_forbidden() -> None:
    """Stub for test_live_status_auth_failed_forbidden."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def live_status_coordinator_refresh_error() -> None:
    """Stub for test_live_status_coordinator_refresh_error."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def energy_history_coordinator_refresh_errors() -> None:
    """Stub for test_energy_history_coordinator_refresh_errors."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def dynamic_device_discovery_triggers_reload() -> None:
    """Stub for test_dynamic_device_discovery_triggers_reload."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def dynamic_device_discovery_no_reload_for_scope_only_change() -> None:
    """Stub for test_dynamic_device_discovery_no_reload_for_scope_only_change."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def dynamic_device_discovery_no_reload_without_changes() -> None:
    """Stub for test_dynamic_device_discovery_no_reload_without_changes."""

