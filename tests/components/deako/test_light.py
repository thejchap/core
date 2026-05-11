"""Tryke skip stub for test_light.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("snapshot test — out of scope")
async def light_setup_with_device() -> None:
    """Stub for test_light_setup_with_device."""


@test.skip("snapshot test — out of scope")
async def light_initial_props() -> None:
    """Stub for test_light_initial_props."""


@test.skip("snapshot test — out of scope")
async def dimmable_light_props() -> None:
    """Stub for test_dimmable_light_props."""


@test.skip("snapshot test — out of scope")
async def light_power_change_on() -> None:
    """Stub for test_light_power_change_on."""


@test.skip("snapshot test — out of scope")
async def light_power_change_off() -> None:
    """Stub for test_light_power_change_off."""


@test.skip("snapshot test — out of scope")
async def light_brightness_change() -> None:
    """Stub for test_light_brightness_change."""


