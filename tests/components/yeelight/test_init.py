"""Tryke skip-stubs for test_init.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("yeelight: sibling test pending tryke port")
async def ip_changes_fallback_discovery() -> None:
    """Stub for test_ip_changes_fallback_discovery."""


@test.skip("yeelight: sibling test pending tryke port")
async def ip_changes_id_missing_cannot_fallback() -> None:
    """Stub for test_ip_changes_id_missing_cannot_fallback."""


@test.skip("yeelight: sibling test pending tryke port")
async def setup_discovery() -> None:
    """Stub for test_setup_discovery."""


@test.skip("yeelight: sibling test pending tryke port")
async def setup_discovery_with_manually_configured_network_adapter() -> None:
    """Stub for test_setup_discovery_with_manually_configured_network_adapter."""


@test.skip("yeelight: sibling test pending tryke port")
async def setup_discovery_with_manually_configured_network_adapter_one_fails() -> None:
    """Stub for test_setup_discovery_with_manually_configured_network_adapter_one_fails."""


@test.skip("yeelight: sibling test pending tryke port")
async def setup_import() -> None:
    """Stub for test_setup_import."""


@test.skip("yeelight: sibling test pending tryke port")
async def unique_ids_device() -> None:
    """Stub for test_unique_ids_device."""


@test.skip("yeelight: sibling test pending tryke port")
async def unique_ids_entry() -> None:
    """Stub for test_unique_ids_entry."""


@test.skip("yeelight: sibling test pending tryke port")
async def bulb_off_while_adding_in_ha() -> None:
    """Stub for test_bulb_off_while_adding_in_ha."""


@test.skip("yeelight: sibling test pending tryke port")
async def async_listen_error_late_discovery() -> None:
    """Stub for test_async_listen_error_late_discovery."""


@test.skip("yeelight: sibling test pending tryke port")
async def fail_to_fetch_initial_state() -> None:
    """Stub for test_fail_to_fetch_initial_state."""


@test.skip("yeelight: sibling test pending tryke port")
async def unload_before_discovery() -> None:
    """Stub for test_unload_before_discovery."""


@test.skip("yeelight: sibling test pending tryke port")
async def async_listen_error_has_host_with_id() -> None:
    """Stub for test_async_listen_error_has_host_with_id."""


@test.skip("yeelight: sibling test pending tryke port")
async def async_listen_error_has_host_without_id() -> None:
    """Stub for test_async_listen_error_has_host_without_id."""


@test.skip("yeelight: sibling test pending tryke port")
async def async_setup_with_missing_id() -> None:
    """Stub for test_async_setup_with_missing_id."""


@test.skip("yeelight: sibling test pending tryke port")
async def async_setup_with_missing_unique_id() -> None:
    """Stub for test_async_setup_with_missing_unique_id."""


@test.skip("yeelight: sibling test pending tryke port")
async def connection_dropped_resyncs_properties() -> None:
    """Stub for test_connection_dropped_resyncs_properties."""


@test.skip("yeelight: sibling test pending tryke port")
async def oserror_on_first_update_results_in_unavailable() -> None:
    """Stub for test_oserror_on_first_update_results_in_unavailable."""


@test.skip("yeelight: sibling test pending tryke port")
async def non_oserror_exception_on_first_update() -> None:
    """Stub for test_non_oserror_exception_on_first_update."""


@test.skip("yeelight: sibling test pending tryke port")
async def async_setup_with_discovery_not_working() -> None:
    """Stub for test_async_setup_with_discovery_not_working."""


@test.skip("yeelight: sibling test pending tryke port")
async def async_setup_retries_with_wrong_device() -> None:
    """Stub for test_async_setup_retries_with_wrong_device."""
