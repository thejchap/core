"""Tryke skip-stubs for opower sensor tests.

Original tests use opower API mocks + recorder + statistics; full port deferred.
"""

from tryke import test

@test.skip("opower API mocks + recorder + statistics")
async def sensors() -> None:
    """Test the creation and values of Opower sensors."""

@test.skip("opower API mocks + recorder + statistics")
async def dynamic_and_stale_devices() -> None:
    """Test the dynamic addition and removal of Opower devices."""

@test.skip("opower API mocks + recorder + statistics")
async def stale_device_removed_on_load() -> None:
    """Test that a stale device present before setup is removed on first load."""
