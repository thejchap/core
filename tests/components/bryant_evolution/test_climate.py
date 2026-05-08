"""Tryke skip stub for test_climate.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def setup_integration_success() -> None:
    """Stub for test_setup_integration_success."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def set_temperature_mode_cool() -> None:
    """Stub for test_set_temperature_mode_cool."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def set_temperature_mode_heat() -> None:
    """Stub for test_set_temperature_mode_heat."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def set_temperature_mode_heat_cool() -> None:
    """Stub for test_set_temperature_mode_heat_cool."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def set_fan_mode() -> None:
    """Stub for test_set_fan_mode."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def set_hvac_mode() -> None:
    """Stub for test_set_hvac_mode."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def read_hvac_action_heat_cool() -> None:
    """Stub for test_read_hvac_action_heat_cool."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def read_hvac_action() -> None:
    """Stub for test_read_hvac_action."""


