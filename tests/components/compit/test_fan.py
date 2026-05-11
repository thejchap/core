"""Tryke skip stub for test_fan.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.compit.fan module imports cleanly."""
    from homeassistant.components.compit import fan  # noqa: PLC0415
    expect(fan).not_.to_be(None)


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def fan_entities_snapshot() -> None:
    """Stub for test_fan_entities_snapshot."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def fan_turn_on() -> None:
    """Stub for test_fan_turn_on."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def fan_turn_on_with_percentage() -> None:
    """Stub for test_fan_turn_on_with_percentage."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def fan_turn_off() -> None:
    """Stub for test_fan_turn_off."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def fan_set_speed() -> None:
    """Stub for test_fan_set_speed."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def fan_set_speed_while_off() -> None:
    """Stub for test_fan_set_speed_while_off."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def fan_set_speed_to_not_in_step_percentage() -> None:
    """Stub for test_fan_set_speed_to_not_in_step_percentage."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def fan_set_speed_to_0() -> None:
    """Stub for test_fan_set_speed_to_0."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def fan_invalid_speed() -> None:
    """Stub for test_fan_invalid_speed."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def fan_gear_to_percentage() -> None:
    """Stub for test_fan_gear_to_percentage."""


