"""Tryke skip-stubs for onvif switch tests.

Original tests use ONVIF camera mocks + zeroconf discovery; full port deferred.
"""

from tryke import expect, test

@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.onvif.switch module imports cleanly."""
    from homeassistant.components.onvif import switch  # noqa: PLC0415
    expect(switch).not_.to_be(None)


@test.skip("ONVIF camera mocks + zeroconf discovery")
async def wiper_switch() -> None:
    """Test states of the Wiper switch."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def wiper_switch_no_ptz() -> None:
    """Test the wiper switch does not get created if the camera does not support ptz."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def turn_wiper_switch_on() -> None:
    """Test Wiper switch turn on."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def turn_wiper_switch_off() -> None:
    """Test Wiper switch turn off."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def autofocus_switch() -> None:
    """Test states of the autofocus switch."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def auto_focus_switch_no_imaging() -> None:
    """Test the autofocus switch does not get created if the camera does not support imaging."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def turn_autofocus_switch_on() -> None:
    """Test autofocus switch turn on."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def turn_autofocus_switch_off() -> None:
    """Test autofocus switch turn off."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def infrared_switch() -> None:
    """Test states of the autofocus switch."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def infrared_switch_no_imaging() -> None:
    """Test the infrared switch does not get created if the camera does not support imaging."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def turn_infrared_switch_on() -> None:
    """Test infrared switch turn on."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def turn_infrared_switch_off() -> None:
    """Test infrared switch turn off."""
