"""Tryke skip stub for test_device_trigger.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def get_triggers() -> None:
    """Stub for test_get_triggers."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def if_fires_on_turn_on_request() -> None:
    """Stub for test_if_fires_on_turn_on_request."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def if_fires_on_turn_on_request_legacy() -> None:
    """Stub for test_if_fires_on_turn_on_request_legacy."""

