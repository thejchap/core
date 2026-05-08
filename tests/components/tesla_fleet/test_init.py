"""Tryke skip-stubs for tesla_fleet/test_init.py."""

from tryke import test


@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def load_unload() -> None:
    """Stub for test_load_unload."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def init_error() -> None:
    """Stub for test_init_error."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def oauth_refresh_expired() -> None:
    """Stub for test_oauth_refresh_expired."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def oauth_refresh_error() -> None:
    """Stub for test_oauth_refresh_error."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def setup_uses_scopes_from_refreshed_token() -> None:
    """Stub for test_setup_uses_scopes_from_refreshed_token."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def invalidate_access_token_updates_when_not_expired() -> None:
    """Stub for test_invalidate_access_token_updates_when_not_expired."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def invalidate_access_token_noop_when_already_expired() -> None:
    """Stub for test_invalidate_access_token_noop_when_already_expired."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def invalidate_access_token_noop_when_token_missing() -> None:
    """Stub for test_invalidate_access_token_noop_when_token_missing."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def devices() -> None:
    """Stub for test_devices."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def vehicle_refresh_offline() -> None:
    """Stub for test_vehicle_refresh_offline."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def vehicle_refresh_error() -> None:
    """Stub for test_vehicle_refresh_error."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def vehicle_refresh_token_expired_recovery() -> None:
    """Stub for test_vehicle_refresh_token_expired_recovery."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def vehicle_refresh_ratelimited() -> None:
    """Stub for test_vehicle_refresh_ratelimited."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def vehicle_refresh_ratelimited_no_after() -> None:
    """Stub for test_vehicle_refresh_ratelimited_no_after."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def init_invalid_region() -> None:
    """Stub for test_init_invalid_region."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def vehicle_sleep() -> None:
    """Stub for test_vehicle_sleep."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def energy_live_refresh_error() -> None:
    """Stub for test_energy_live_refresh_error."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def energy_live_refresh_bad_response() -> None:
    """Stub for test_energy_live_refresh_bad_response."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def energy_live_refresh_bad_wall_connectors() -> None:
    """Stub for test_energy_live_refresh_bad_wall_connectors."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def energy_site_refresh_error() -> None:
    """Stub for test_energy_site_refresh_error."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def energy_refresh_token_expired_recovery() -> None:
    """Stub for test_energy_refresh_token_expired_recovery."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def energy_history_refresh_error() -> None:
    """Stub for test_energy_history_refresh_error."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def energy_live_refresh_ratelimited() -> None:
    """Stub for test_energy_live_refresh_ratelimited."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def energy_info_refresh_ratelimited() -> None:
    """Stub for test_energy_info_refresh_ratelimited."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def energy_history_refresh_ratelimited() -> None:
    """Stub for test_energy_history_refresh_ratelimited."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def init_region_issue() -> None:
    """Stub for test_init_region_issue."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def init_region_issue_failed() -> None:
    """Stub for test_init_region_issue_failed."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def signing() -> None:
    """Stub for test_signing."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def bad_implementation() -> None:
    """Stub for test_bad_implementation."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def vehicle_without_location_scope() -> None:
    """Stub for test_vehicle_without_location_scope."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def vehicle_with_location_scope() -> None:
    """Stub for test_vehicle_with_location_scope."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def oauth_implementation_not_available() -> None:
    """Stub for test_oauth_implementation_not_available."""

