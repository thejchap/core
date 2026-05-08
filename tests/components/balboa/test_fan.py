"""Tryke skip stub for test_fan.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def fan() -> None:
    """Stub for test_fan."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def pump() -> None:
    """Stub for test_pump."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def pump_unknown_state() -> None:
    """Stub for test_pump_unknown_state."""


