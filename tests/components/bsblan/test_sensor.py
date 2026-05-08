"""Tryke skip stub for test_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor_entity_properties() -> None:
    """Stub for test_sensor_entity_properties."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensors_not_created_when_data_unavailable() -> None:
    """Stub for test_sensors_not_created_when_data_unavailable."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def partial_sensors_created_when_some_data_available() -> None:
    """Stub for test_partial_sensors_created_when_some_data_available."""


