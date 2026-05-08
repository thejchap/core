"""Tryke skip stub for test_switch.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def entities() -> None:
    """Stub for test_entities."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def switch_actions() -> None:
    """Stub for test_switch_actions."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def switch_callbacks() -> None:
    """Stub for test_switch_callbacks."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def no_switch_found() -> None:
    """Stub for test_no_switch_found."""


