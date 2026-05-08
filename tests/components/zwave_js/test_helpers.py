"""Tryke skip-stubs for test_helpers.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def async_get_node_status_sensor_entity_id() -> None:
    """Stub for test_async_get_node_status_sensor_entity_id."""


@test.skip("zwave_js: sibling test pending tryke port")
async def async_get_nodes_from_area_id() -> None:
    """Stub for test_async_get_nodes_from_area_id."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_value_state_schema_boolean_config_value() -> None:
    """Stub for test_get_value_state_schema_boolean_config_value."""


@test.skip("zwave_js: sibling test pending tryke port")
async def async_get_provisioning_entry_from_device_id() -> None:
    """Stub for test_async_get_provisioning_entry_from_device_id."""


@test.skip("zwave_js: sibling test pending tryke port")
async def format_home_id_for_display() -> None:
    """Stub for test_format_home_id_for_display."""
