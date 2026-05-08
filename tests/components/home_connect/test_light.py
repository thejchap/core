"""Tryke skip-stubs for test_light.py - indirect parametrize unsupported."""

from tryke import test

@test.skip("indirect parametrize unsupported")
async def paired_depaired_devices_flow() -> None:
    """Stub for test_paired_depaired_devices_flow."""

@test.skip("indirect parametrize unsupported")
async def connected_devices() -> None:
    """Stub for test_connected_devices."""

@test.skip("indirect parametrize unsupported")
async def light_availability() -> None:
    """Stub for test_light_availability."""

@test.skip("indirect parametrize unsupported")
async def light_functionality() -> None:
    """Stub for test_light_functionality."""

@test.skip("indirect parametrize unsupported")
async def light_color_different_than_custom() -> None:
    """Stub for test_light_color_different_than_custom."""

@test.skip("indirect parametrize unsupported")
async def light_exception_handling() -> None:
    """Stub for test_light_exception_handling."""
