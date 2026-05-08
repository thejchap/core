"""Tryke skip-stubs for motionblinds_ble init tests."""

from tryke import test


@test.skip("bluetooth-stack tests — fixtures not in shim")
async def init_placeholder() -> None:
    """Placeholder skipped sibling tests for test_init.py."""
