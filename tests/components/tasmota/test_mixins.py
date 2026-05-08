"""Tryke skip-stubs for tasmota/test_mixins.py."""

from tryke import test


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def availability_poll_state_once() -> None:
    """Stub for test_availability_poll_state_once."""

