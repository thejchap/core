"""Tryke skip-stubs for test_device_trigger.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def no_controller_triggers() -> None:
    """Stub for test_no_controller_triggers."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_notification_notification_triggers() -> None:
    """Stub for test_get_notification_notification_triggers."""


@test.skip("zwave_js: sibling test pending tryke port")
async def if_notification_notification_fires() -> None:
    """Stub for test_if_notification_notification_fires."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_trigger_capabilities_notification_notification() -> None:
    """Stub for test_get_trigger_capabilities_notification_notification."""


@test.skip("zwave_js: sibling test pending tryke port")
async def if_entry_control_notification_fires() -> None:
    """Stub for test_if_entry_control_notification_fires."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_trigger_capabilities_entry_control_notification() -> None:
    """Stub for test_get_trigger_capabilities_entry_control_notification."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_node_status_triggers() -> None:
    """Stub for test_get_node_status_triggers."""


@test.skip("zwave_js: sibling test pending tryke port")
async def if_node_status_change_fires() -> None:
    """Stub for test_if_node_status_change_fires."""


@test.skip("zwave_js: sibling test pending tryke port")
async def if_node_status_change_fires_legacy() -> None:
    """Stub for test_if_node_status_change_fires_legacy."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_trigger_capabilities_node_status() -> None:
    """Stub for test_get_trigger_capabilities_node_status."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_basic_value_notification_triggers() -> None:
    """Stub for test_get_basic_value_notification_triggers."""


@test.skip("zwave_js: sibling test pending tryke port")
async def if_basic_value_notification_fires() -> None:
    """Stub for test_if_basic_value_notification_fires."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_trigger_capabilities_basic_value_notification() -> None:
    """Stub for test_get_trigger_capabilities_basic_value_notification."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_central_scene_value_notification_triggers() -> None:
    """Stub for test_get_central_scene_value_notification_triggers."""


@test.skip("zwave_js: sibling test pending tryke port")
async def if_central_scene_value_notification_fires() -> None:
    """Stub for test_if_central_scene_value_notification_fires."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_trigger_capabilities_central_scene_value_notification() -> None:
    """Stub for test_get_trigger_capabilities_central_scene_value_notification."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_scene_activation_value_notification_triggers() -> None:
    """Stub for test_get_scene_activation_value_notification_triggers."""


@test.skip("zwave_js: sibling test pending tryke port")
async def if_scene_activation_value_notification_fires() -> None:
    """Stub for test_if_scene_activation_value_notification_fires."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_trigger_capabilities_scene_activation_value_notification() -> None:
    """Stub for test_get_trigger_capabilities_scene_activation_value_notification."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_value_updated_value_triggers() -> None:
    """Stub for test_get_value_updated_value_triggers."""


@test.skip("zwave_js: sibling test pending tryke port")
async def if_value_updated_value_fires() -> None:
    """Stub for test_if_value_updated_value_fires."""


@test.skip("zwave_js: sibling test pending tryke port")
async def value_updated_value_no_driver() -> None:
    """Stub for test_value_updated_value_no_driver."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_trigger_capabilities_value_updated_value() -> None:
    """Stub for test_get_trigger_capabilities_value_updated_value."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_value_updated_config_parameter_triggers() -> None:
    """Stub for test_get_value_updated_config_parameter_triggers."""


@test.skip("zwave_js: sibling test pending tryke port")
async def if_value_updated_config_parameter_fires() -> None:
    """Stub for test_if_value_updated_config_parameter_fires."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_trigger_capabilities_value_updated_config_parameter_range() -> None:
    """Stub for test_get_trigger_capabilities_value_updated_config_parameter_range."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_trigger_capabilities_value_updated_config_parameter_enumerated() -> None:
    """Stub for test_get_trigger_capabilities_value_updated_config_parameter_enumerated."""


@test.skip("zwave_js: sibling test pending tryke port")
async def failure_scenarios() -> None:
    """Stub for test_failure_scenarios."""


@test.skip("zwave_js: sibling test pending tryke port")
async def trigger_schema_coerces_string_values() -> None:
    """Stub for test_trigger_schema_coerces_string_values."""
