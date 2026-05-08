"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def august_api_is_failing() -> None:
    """Stub for test_august_api_is_failing."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def august_is_offline() -> None:
    """Stub for test_august_is_offline."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def august_late_auth_failure() -> None:
    """Stub for test_august_late_auth_failure."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unlock_throws_august_api_http_error() -> None:
    """Stub for test_unlock_throws_august_api_http_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def lock_throws_august_api_http_error() -> None:
    """Stub for test_lock_throws_august_api_http_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def open_throws_hass_service_not_supported_error() -> None:
    """Stub for test_open_throws_hass_service_not_supported_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def inoperative_locks_are_filtered_out() -> None:
    """Stub for test_inoperative_locks_are_filtered_out."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def lock_has_doorsense() -> None:
    """Stub for test_lock_has_doorsense."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def load_unload() -> None:
    """Stub for test_load_unload."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def load_triggers_ble_discovery() -> None:
    """Stub for test_load_triggers_ble_discovery."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def device_remove_devices() -> None:
    """Stub for test_device_remove_devices."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def brand_migration_issue() -> None:
    """Stub for test_brand_migration_issue."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def oauth_migration_on_legacy_entry() -> None:
    """Stub for test_oauth_migration_on_legacy_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def oauth_implementation_not_available() -> None:
    """Stub for test_oauth_implementation_not_available."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def oauth_token_request_reauth_error() -> None:
    """Stub for test_oauth_token_request_reauth_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def oauth_token_request_transient_error_is_retryable() -> None:
    """Stub for test_oauth_token_request_transient_error_is_retryable."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def oauth_client_error_is_retryable() -> None:
    """Stub for test_oauth_client_error_is_retryable."""

