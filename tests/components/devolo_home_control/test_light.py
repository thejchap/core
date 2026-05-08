"""Tryke skip stub for test_light.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def light_without_binary_sensor() -> None:
    """Stub for test_light_without_binary_sensor."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def light_with_binary_sensor() -> None:
    """Stub for test_light_with_binary_sensor."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def remove_from_hass() -> None:
    """Stub for test_remove_from_hass."""


