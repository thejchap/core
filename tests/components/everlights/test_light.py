"""The tests for the everlights component."""

from tryke import expect, test

from homeassistant.components.everlights import light as everlights


@test
def color_rgb_to_int() -> None:
    """Test RGB to integer conversion."""
    expect(everlights.color_rgb_to_int(0x00, 0x00, 0x00)).to_equal(0x000000)
    expect(everlights.color_rgb_to_int(0xFF, 0xFF, 0xFF)).to_equal(0xFFFFFF)
    expect(everlights.color_rgb_to_int(0x12, 0x34, 0x56)).to_equal(0x123456)


@test
def int_to_rgb() -> None:
    """Test integer to RGB conversion."""
    expect(everlights.color_int_to_rgb(0x000000)).to_equal((0x00, 0x00, 0x00))
    expect(everlights.color_int_to_rgb(0xFFFFFF)).to_equal((0xFF, 0xFF, 0xFF))
    expect(everlights.color_int_to_rgb(0x123456)).to_equal((0x12, 0x34, 0x56))
