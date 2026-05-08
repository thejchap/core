"""Tryke skip-stubs for test_binary_sensor.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def battery_sensors() -> None:
    """Stub for test_battery_sensors."""


@test.skip("zwave_js: sibling test pending tryke port")
async def enabled_legacy_sensor() -> None:
    """Stub for test_enabled_legacy_sensor."""


@test.skip("zwave_js: sibling test pending tryke port")
async def disabled_legacy_sensor() -> None:
    """Stub for test_disabled_legacy_sensor."""


@test.skip("zwave_js: sibling test pending tryke port")
async def notification_sensor() -> None:
    """Stub for test_notification_sensor."""


@test.skip("zwave_js: sibling test pending tryke port")
async def notification_off_state() -> None:
    """Stub for test_notification_off_state."""


@test.skip("zwave_js: sibling test pending tryke port")
async def property_sensor_door_status() -> None:
    """Stub for test_property_sensor_door_status."""


@test.skip("zwave_js: sibling test pending tryke port")
async def opening_state_creates_open_binary_sensor() -> None:
    """Stub for test_opening_state_creates_open_binary_sensor."""


@test.skip("zwave_js: sibling test pending tryke port")
async def opening_state_disables_legacy_window_door_notification_sensors() -> None:
    """Stub for test_opening_state_disables_legacy_window_door_notification_sensors."""


@test.skip("zwave_js: sibling test pending tryke port")
async def opening_state_binary_sensors_with_tilted() -> None:
    """Stub for test_opening_state_binary_sensors_with_tilted."""


@test.skip("zwave_js: sibling test pending tryke port")
async def opening_state_tilted_appears_via_metadata_update() -> None:
    """Stub for test_opening_state_tilted_appears_via_metadata_update."""


@test.skip("zwave_js: sibling test pending tryke port")
async def reenabled_legacy_door_state_entity_follows_opening_state() -> None:
    """Stub for test_reenabled_legacy_door_state_entity_follows_opening_state."""


@test.skip("zwave_js: sibling test pending tryke port")
async def legacy_door_state_entities_follow_opening_state() -> None:
    """Stub for test_legacy_door_state_entities_follow_opening_state."""


@test.skip("zwave_js: sibling test pending tryke port")
async def legacy_door_state_non_zero_endpoint() -> None:
    """Stub for test_legacy_door_state_non_zero_endpoint."""


@test.skip("zwave_js: sibling test pending tryke port")
async def access_control_lock_state_notification_sensors() -> None:
    """Stub for test_access_control_lock_state_notification_sensors."""


@test.skip("zwave_js: sibling test pending tryke port")
async def access_control_catch_all_with_opening_state_present() -> None:
    """Stub for test_access_control_catch_all_with_opening_state_present."""


@test.skip("zwave_js: sibling test pending tryke port")
async def config_parameter_binary_sensor() -> None:
    """Stub for test_config_parameter_binary_sensor."""


@test.skip("zwave_js: sibling test pending tryke port")
async def smoke_co_notification_sensors() -> None:
    """Stub for test_smoke_co_notification_sensors."""


@test.skip("zwave_js: sibling test pending tryke port")
async def hoppe_ehandle_connectsense() -> None:
    """Stub for test_hoppe_ehandle_connectsense."""


@test.skip("zwave_js: sibling test pending tryke port")
async def legacy_door_open_state_repair_issue() -> None:
    """Stub for test_legacy_door_open_state_repair_issue."""


@test.skip("zwave_js: sibling test pending tryke port")
async def legacy_door_tilt_state_repair_issue() -> None:
    """Stub for test_legacy_door_tilt_state_repair_issue."""


@test.skip("zwave_js: sibling test pending tryke port")
async def legacy_door_open_state_no_repair_issue_when_disabled() -> None:
    """Stub for test_legacy_door_open_state_no_repair_issue_when_disabled."""


@test.skip("zwave_js: sibling test pending tryke port")
async def legacy_closed_door_state_does_not_create_repair_issue() -> None:
    """Stub for test_legacy_closed_door_state_does_not_create_repair_issue."""


@test.skip("zwave_js: sibling test pending tryke port")
async def hoppe_custom_tilt_sensor_no_repair_issue() -> None:
    """Stub for test_hoppe_custom_tilt_sensor_no_repair_issue."""


@test.skip("zwave_js: sibling test pending tryke port")
async def legacy_door_open_state_stale_repair_issue_cleaned_up() -> None:
    """Stub for test_legacy_door_open_state_stale_repair_issue_cleaned_up."""
