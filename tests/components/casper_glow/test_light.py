"""Tryke skip stub for test_light.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def entities() -> None:
    """Stub for test_entities."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def turn_on() -> None:
    """Stub for test_turn_on."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def turn_off() -> None:
    """Stub for test_turn_off."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def state_update_via_callback() -> None:
    """Stub for test_state_update_via_callback."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def color_mode() -> None:
    """Stub for test_color_mode."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def brightness_snap_to_nearest() -> None:
    """Stub for test_brightness_snap_to_nearest."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def brightness_update_via_callback() -> None:
    """Stub for test_brightness_update_via_callback."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def command_error() -> None:
    """Stub for test_command_error."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def state_update_via_callback_after_command_failure() -> None:
    """Stub for test_state_update_via_callback_after_command_failure."""


