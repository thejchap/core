"""Tryke skip-stubs for onvif button tests.

Original tests use ONVIF camera mocks + zeroconf discovery; full port deferred.
"""

from tryke import test

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def reboot_button() -> None:
    """Test states of the Reboot button."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def reboot_button_press() -> None:
    """Test Reboot button press."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def set_dateandtime_button() -> None:
    """Test states of the SetDateAndTime button."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def set_dateandtime_button_press() -> None:
    """Test SetDateAndTime button press."""
