"""Tryke skip stub for test_switch.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def all_entities() -> None:
    """Stub for test_all_entities."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def switch_set_state() -> None:
    """Stub for test_switch_set_state."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def switch_dynamic() -> None:
    """Stub for test_switch_dynamic."""


