"""Tryke skip-stubs for otbr config flow tests.

Original tests use supervisor_client fixture; full port deferred.
"""

from tryke import test

@test.skip("supervisor_client fixture")
async def user_flow() -> None:
    """Stub for test_user_flow (port deferred)."""

@test.skip("supervisor_client fixture")
async def user_flow_additional_entry() -> None:
    """Stub for test_user_flow_additional_entry (port deferred)."""

@test.skip("supervisor_client fixture")
async def user_flow_additional_entry_fail_get_address() -> None:
    """Stub for test_user_flow_additional_entry_fail_get_address (port deferred)."""

@test.skip("supervisor_client fixture")
async def user_flow_additional_entry_same_address() -> None:
    """Stub for test_user_flow_additional_entry_same_address (port deferred)."""

@test.skip("supervisor_client fixture")
async def user_flow_router_not_setup() -> None:
    """Stub for test_user_flow_router_not_setup (port deferred)."""

@test.skip("supervisor_client fixture")
async def user_flow_get_dataset_404() -> None:
    """Stub for test_user_flow_get_dataset_404 (port deferred)."""

@test.skip("supervisor_client fixture")
async def user_flow_get_ba_id_connect_error() -> None:
    """Stub for test_user_flow_get_ba_id_connect_error (port deferred)."""

@test.skip("supervisor_client fixture")
async def user_flow_get_dataset_connect_error() -> None:
    """Stub for test_user_flow_get_dataset_connect_error (port deferred)."""

@test.skip("supervisor_client fixture")
async def hassio_discovery_flow() -> None:
    """Stub for test_hassio_discovery_flow (port deferred)."""

@test.skip("supervisor_client fixture")
async def hassio_discovery_flow_yellow() -> None:
    """Stub for test_hassio_discovery_flow_yellow (port deferred)."""

@test.skip("supervisor_client fixture")
async def hassio_discovery_flow_sky_connect() -> None:
    """Stub for test_hassio_discovery_flow_sky_connect (port deferred)."""

@test.skip("supervisor_client fixture")
async def hassio_discovery_flow_2x_addons() -> None:
    """Stub for test_hassio_discovery_flow_2x_addons (port deferred)."""

@test.skip("supervisor_client fixture")
async def hassio_discovery_flow_2x_addons_same_ext_address() -> None:
    """Stub for test_hassio_discovery_flow_2x_addons_same_ext_address (port deferred)."""

@test.skip("supervisor_client fixture")
async def hassio_discovery_flow_router_not_setup() -> None:
    """Stub for test_hassio_discovery_flow_router_not_setup (port deferred)."""

@test.skip("supervisor_client fixture")
async def hassio_discovery_flow_router_not_setup_has_preferred() -> None:
    """Stub for test_hassio_discovery_flow_router_not_setup_has_preferred (port deferred)."""

@test.skip("supervisor_client fixture")
async def hassio_discovery_flow_router_not_setup_has_preferred_2() -> None:
    """Stub for test_hassio_discovery_flow_router_not_setup_has_preferred_2 (port deferred)."""

@test.skip("supervisor_client fixture")
async def hassio_discovery_flow_404() -> None:
    """Stub for test_hassio_discovery_flow_404 (port deferred)."""

@test.skip("supervisor_client fixture")
async def hassio_discovery_flow_new_port_missing_unique_id() -> None:
    """Stub for test_hassio_discovery_flow_new_port_missing_unique_id (port deferred)."""

@test.skip("supervisor_client fixture")
async def hassio_discovery_flow_new_port() -> None:
    """Stub for test_hassio_discovery_flow_new_port (port deferred)."""

@test.skip("supervisor_client fixture")
async def hassio_discovery_flow_new_port_other_addon() -> None:
    """Stub for test_hassio_discovery_flow_new_port_other_addon (port deferred)."""

@test.skip("supervisor_client fixture")
async def config_flow_additional_entry() -> None:
    """Stub for test_config_flow_additional_entry (port deferred)."""

@test.skip("supervisor_client fixture")
async def hassio_discovery_reload() -> None:
    """Stub for test_hassio_discovery_reload (port deferred)."""
