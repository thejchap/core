"""Tryke skip-stubs for test_hardware.py - supervisor_client beyond shim slice."""

from tryke import test

@test.skip("supervisor_client beyond shim slice")
async def hardware_info() -> None:
    """Stub for test_hardware_info."""

@test.skip("supervisor_client beyond shim slice")
async def hardware_info_fail() -> None:
    """Stub for test_hardware_info_fail."""
