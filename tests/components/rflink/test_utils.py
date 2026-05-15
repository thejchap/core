"""Tryke skip stub (pending port)."""

from tryke import expect, test

from homeassistant.components.rflink.utils import (
    brightness_to_rflink,
    rflink_to_brightness,
)


@test
async def utils() -> None:
    """Test all utils methods."""
    # test brightness_to_rflink
    expect(brightness_to_rflink(0)).to_equal(0)
    expect(brightness_to_rflink(17)).to_equal(1)
    expect(brightness_to_rflink(34)).to_equal(2)
    expect(brightness_to_rflink(85)).to_equal(5)
    expect(brightness_to_rflink(170)).to_equal(10)
    expect(brightness_to_rflink(255)).to_equal(15)

    expect(brightness_to_rflink(10)).to_equal(0)
    expect(brightness_to_rflink(20)).to_equal(1)
    expect(brightness_to_rflink(30)).to_equal(1)
    expect(brightness_to_rflink(40)).to_equal(2)
    expect(brightness_to_rflink(50)).to_equal(2)
    expect(brightness_to_rflink(60)).to_equal(3)
    expect(brightness_to_rflink(70)).to_equal(4)
    expect(brightness_to_rflink(80)).to_equal(4)

    # test rflink_to_brightness
    expect(rflink_to_brightness(0)).to_equal(0)
    expect(rflink_to_brightness(1)).to_equal(17)
    expect(rflink_to_brightness(5)).to_equal(85)
    expect(rflink_to_brightness(10)).to_equal(170)
    expect(rflink_to_brightness(12)).to_equal(204)
    expect(rflink_to_brightness(15)).to_equal(255)
