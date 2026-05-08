"""Tryke skip stub for test_switch.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switches() -> None:
    """Stub for test_switches."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switches_mqtt_update() -> None:
    """Stub for test_switches_mqtt_update."""

