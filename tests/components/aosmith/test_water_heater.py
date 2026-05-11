"""Tryke skip stub for test_water_heater.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("snapshot test — out of scope")
async def state() -> None:
    """Stub for test_state."""


@test.skip("snapshot test — out of scope")
async def state_away_mode_unsupported() -> None:
    """Stub for test_state_away_mode_unsupported."""


@test.skip("snapshot test — out of scope")
async def set_operation_mode() -> None:
    """Stub for test_set_operation_mode."""


@test.skip("snapshot test — out of scope")
async def unsupported_operation_mode() -> None:
    """Stub for test_unsupported_operation_mode."""


@test.skip("snapshot test — out of scope")
async def set_temperature() -> None:
    """Stub for test_set_temperature."""


@test.skip("snapshot test — out of scope")
async def away_mode() -> None:
    """Stub for test_away_mode."""


