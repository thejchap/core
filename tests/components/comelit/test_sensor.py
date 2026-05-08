"""Tryke skip stub for test_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def all_entities() -> None:
    """Stub for test_all_entities."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor_state_unknown() -> None:
    """Stub for test_sensor_state_unknown."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def serial_bridge_sensor_dynamic() -> None:
    """Stub for test_serial_bridge_sensor_dynamic."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def vedo_sensor_dynamic() -> None:
    """Stub for test_vedo_sensor_dynamic."""


