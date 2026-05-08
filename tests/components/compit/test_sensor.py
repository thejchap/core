"""Tryke skip stub for test_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor_entities_snapshot() -> None:
    """Stub for test_sensor_entities_snapshot."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor_return_value_enum_sensor() -> None:
    """Stub for test_sensor_return_value_enum_sensor."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor_enum_value_cannot_return_number() -> None:
    """Stub for test_sensor_enum_value_cannot_return_number."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor_return_value_number_sensor() -> None:
    """Stub for test_sensor_return_value_number_sensor."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor_number_value_cannot_return_enum() -> None:
    """Stub for test_sensor_number_value_cannot_return_enum."""


