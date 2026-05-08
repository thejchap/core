"""Tryke skip stub for test_alarm_control_panel.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def entity_availability() -> None:
    """Stub for test_entity_availability."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def arming_disarming() -> None:
    """Stub for test_arming_disarming."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def wrong_code() -> None:
    """Stub for test_wrong_code."""

