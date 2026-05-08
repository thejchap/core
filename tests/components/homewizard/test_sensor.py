"""Tryke skip-stubs for test_sensor.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def sensors() -> None:
    """Stub for test_sensors."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def disabled_by_default_sensors() -> None:
    """Stub for test_disabled_by_default_sensors."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def sensors_unreachable() -> None:
    """Stub for test_sensors_unreachable."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def external_sensors_unreachable() -> None:
    """Stub for test_external_sensors_unreachable."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def entities_not_created_for_device() -> None:
    """Stub for test_entities_not_created_for_device."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def uptime_sensor_does_not_update_timestamp_on_data_update() -> None:
    """Stub for test_uptime_sensor_does_not_update_timestamp_on_data_update."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def uptime_sensor_does_not_update_timestamp_on_minor_change() -> None:
    """Stub for test_uptime_sensor_does_not_update_timestamp_on_minor_change."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def uptime_sensor_refreshes_when_detecting_reboot() -> None:
    """Stub for test_uptime_sensor_refreshes_when_detecting_reboot."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def uptime_sensor_unavailable() -> None:
    """Stub for test_uptime_sensor_unavailable."""
