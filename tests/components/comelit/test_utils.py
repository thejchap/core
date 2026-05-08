"""Tryke skip stub for test_utils.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def device_remove_stale() -> None:
    """Stub for test_device_remove_stale."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def bridge_api_call_exceptions() -> None:
    """Stub for test_bridge_api_call_exceptions."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def bridge_api_call_reauth() -> None:
    """Stub for test_bridge_api_call_reauth."""

