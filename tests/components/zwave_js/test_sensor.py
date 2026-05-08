"""Tryke skip-stubs for test_sensor.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def battery_sensors() -> None:
    """Stub for test_battery_sensors."""


@test.skip("zwave_js: sibling test pending tryke port")
async def numeric_sensor() -> None:
    """Stub for test_numeric_sensor."""


@test.skip("zwave_js: sibling test pending tryke port")
async def invalid_multilevel_sensor_scale() -> None:
    """Stub for test_invalid_multilevel_sensor_scale."""


@test.skip("zwave_js: sibling test pending tryke port")
async def energy_sensors() -> None:
    """Stub for test_energy_sensors."""


@test.skip("zwave_js: sibling test pending tryke port")
async def basic_cc_sensor() -> None:
    """Stub for test_basic_cc_sensor."""


@test.skip("zwave_js: sibling test pending tryke port")
async def config_parameter_sensor() -> None:
    """Stub for test_config_parameter_sensor."""


@test.skip("zwave_js: sibling test pending tryke port")
async def controller_status_sensor() -> None:
    """Stub for test_controller_status_sensor."""


@test.skip("zwave_js: sibling test pending tryke port")
async def node_status_sensor() -> None:
    """Stub for test_node_status_sensor."""


@test.skip("zwave_js: sibling test pending tryke port")
async def node_status_sensor_not_ready() -> None:
    """Stub for test_node_status_sensor_not_ready."""


@test.skip("zwave_js: sibling test pending tryke port")
async def reset_meter() -> None:
    """Stub for test_reset_meter."""


@test.skip("zwave_js: sibling test pending tryke port")
async def meter_attributes() -> None:
    """Stub for test_meter_attributes."""


@test.skip("zwave_js: sibling test pending tryke port")
async def invalid_meter_scale() -> None:
    """Stub for test_invalid_meter_scale."""


@test.skip("zwave_js: sibling test pending tryke port")
async def special_meters() -> None:
    """Stub for test_special_meters."""


@test.skip("zwave_js: sibling test pending tryke port")
async def unit_change() -> None:
    """Stub for test_unit_change."""


@test.skip("zwave_js: sibling test pending tryke port")
async def new_sensor_invalid_scale() -> None:
    """Stub for test_new_sensor_invalid_scale."""


@test.skip("zwave_js: sibling test pending tryke port")
async def statistics_sensors_migration() -> None:
    """Stub for test_statistics_sensors_migration."""


@test.skip("zwave_js: sibling test pending tryke port")
async def statistics_sensors() -> None:
    """Stub for test_statistics_sensors."""


@test.skip("zwave_js: sibling test pending tryke port")
async def last_seen_statistics_sensors() -> None:
    """Stub for test_last_seen_statistics_sensors."""


@test.skip("zwave_js: sibling test pending tryke port")
async def rssi_sensor_error() -> None:
    """Stub for test_rssi_sensor_error."""


@test.skip("zwave_js: sibling test pending tryke port")
async def energy_production_sensors() -> None:
    """Stub for test_energy_production_sensors."""
