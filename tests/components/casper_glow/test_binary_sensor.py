"""Tryke skip stub for test_binary_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def entities() -> None:
    """Stub for test_entities."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def paused_state_update() -> None:
    """Stub for test_paused_state_update."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def paused_ignores_none_state() -> None:
    """Stub for test_paused_ignores_none_state."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def charging_state_update() -> None:
    """Stub for test_charging_state_update."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def charging_ignores_none_state() -> None:
    """Stub for test_charging_ignores_none_state."""


