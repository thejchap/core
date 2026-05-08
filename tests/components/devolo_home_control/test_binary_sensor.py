"""Tryke skip stub for test_binary_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def binary_sensor() -> None:
    """Stub for test_binary_sensor."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def remote_control() -> None:
    """Stub for test_remote_control."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def disabled() -> None:
    """Stub for test_disabled."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def remove_from_hass() -> None:
    """Stub for test_remove_from_hass."""


