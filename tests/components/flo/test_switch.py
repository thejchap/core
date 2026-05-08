"""Tryke skip stub for test_switch.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def valve_switches() -> None:
    """Stub for test_valve_switches."""

