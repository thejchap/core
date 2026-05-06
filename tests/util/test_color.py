"""Test Home Assistant color util methods."""

import math

from tryke import expect, test
import voluptuous as vol

from homeassistant.util import color as color_util

GAMUT = color_util.GamutType(
    color_util.XYPoint(0.704, 0.296),
    color_util.XYPoint(0.2151, 0.7106),
    color_util.XYPoint(0.138, 0.08),
)
GAMUT_INVALID_1 = color_util.GamutType(
    color_util.XYPoint(0.704, 0.296),
    color_util.XYPoint(-0.201, 0.7106),
    color_util.XYPoint(0.138, 0.08),
)
GAMUT_INVALID_2 = color_util.GamutType(
    color_util.XYPoint(0.704, 1.296),
    color_util.XYPoint(0.2151, 0.7106),
    color_util.XYPoint(0.138, 0.08),
)
GAMUT_INVALID_3 = color_util.GamutType(
    color_util.XYPoint(0.0, 0.0),
    color_util.XYPoint(0.0, 0.0),
    color_util.XYPoint(0.0, 0.0),
)
GAMUT_INVALID_4 = color_util.GamutType(
    color_util.XYPoint(0.1, 0.1),
    color_util.XYPoint(0.3, 0.3),
    color_util.XYPoint(0.7, 0.7),
)


@test
def color_RGB_to_xy_brightness() -> None:
    """Test color_RGB_to_xy_brightness."""
    expect(color_util.color_RGB_to_xy_brightness(0, 0, 0)).to_equal((0, 0, 0))
    expect(color_util.color_RGB_to_xy_brightness(255, 255, 255)).to_equal(
        (0.323, 0.329, 255)
    )

    expect(color_util.color_RGB_to_xy_brightness(0, 0, 255)).to_equal((0.136, 0.04, 12))

    expect(color_util.color_RGB_to_xy_brightness(0, 255, 0)).to_equal(
        (0.172, 0.747, 170)
    )

    expect(color_util.color_RGB_to_xy_brightness(255, 0, 0)).to_equal(
        (0.701, 0.299, 72)
    )

    expect(color_util.color_RGB_to_xy_brightness(128, 0, 0)).to_equal(
        (0.701, 0.299, 16)
    )

    expect(color_util.color_RGB_to_xy_brightness(255, 0, 0, GAMUT)).to_equal(
        (0.7, 0.299, 72)
    )

    expect(color_util.color_RGB_to_xy_brightness(0, 255, 0, GAMUT)).to_equal(
        (0.215, 0.711, 170)
    )

    expect(color_util.color_RGB_to_xy_brightness(0, 0, 255, GAMUT)).to_equal(
        (0.138, 0.08, 12)
    )


@test
def color_RGB_to_xy() -> None:
    """Test color_RGB_to_xy."""
    expect(color_util.color_RGB_to_xy(0, 0, 0)).to_equal((0, 0))
    expect(color_util.color_RGB_to_xy(255, 255, 255)).to_equal((0.323, 0.329))

    expect(color_util.color_RGB_to_xy(0, 0, 255)).to_equal((0.136, 0.04))

    expect(color_util.color_RGB_to_xy(0, 255, 0)).to_equal((0.172, 0.747))

    expect(color_util.color_RGB_to_xy(255, 0, 0)).to_equal((0.701, 0.299))

    expect(color_util.color_RGB_to_xy(128, 0, 0)).to_equal((0.701, 0.299))

    expect(color_util.color_RGB_to_xy(0, 0, 255, GAMUT)).to_equal((0.138, 0.08))

    expect(color_util.color_RGB_to_xy(0, 255, 0, GAMUT)).to_equal((0.215, 0.711))

    expect(color_util.color_RGB_to_xy(255, 0, 0, GAMUT)).to_equal((0.7, 0.299))


@test
def color_xy_brightness_to_RGB() -> None:
    """Test color_xy_brightness_to_RGB."""
    expect(color_util.color_xy_brightness_to_RGB(1, 1, 0)).to_equal((0, 0, 0))

    expect(color_util.color_xy_brightness_to_RGB(0.35, 0.35, 128)).to_equal(
        (194, 186, 169)
    )

    expect(color_util.color_xy_brightness_to_RGB(0.35, 0.35, 255)).to_equal(
        (255, 243, 222)
    )

    expect(color_util.color_xy_brightness_to_RGB(1, 0, 255)).to_equal((255, 0, 60))

    expect(color_util.color_xy_brightness_to_RGB(0, 1, 255)).to_equal((0, 255, 0))

    expect(color_util.color_xy_brightness_to_RGB(0, 0, 255)).to_equal((0, 63, 255))

    expect(color_util.color_xy_brightness_to_RGB(1, 0, 255, GAMUT)).to_equal(
        (255, 0, 3)
    )

    expect(color_util.color_xy_brightness_to_RGB(0, 1, 255, GAMUT)).to_equal(
        (82, 255, 0)
    )

    expect(color_util.color_xy_brightness_to_RGB(0, 0, 255, GAMUT)).to_equal(
        (9, 85, 255)
    )


@test
def color_xy_to_RGB() -> None:
    """Test color_xy_to_RGB."""
    expect(color_util.color_xy_to_RGB(0.35, 0.35)).to_equal((255, 243, 222))

    expect(color_util.color_xy_to_RGB(1, 0)).to_equal((255, 0, 60))

    expect(color_util.color_xy_to_RGB(0, 1)).to_equal((0, 255, 0))

    expect(color_util.color_xy_to_RGB(0, 0)).to_equal((0, 63, 255))

    expect(color_util.color_xy_to_RGB(1, 0, GAMUT)).to_equal((255, 0, 3))

    expect(color_util.color_xy_to_RGB(0, 1, GAMUT)).to_equal((82, 255, 0))

    expect(color_util.color_xy_to_RGB(0, 0, GAMUT)).to_equal((9, 85, 255))


@test
def color_RGB_to_hsv() -> None:
    """Test color_RGB_to_hsv."""
    expect(color_util.color_RGB_to_hsv(0, 0, 0)).to_equal((0, 0, 0))

    expect(color_util.color_RGB_to_hsv(255, 255, 255)).to_equal((0, 0, 100))

    expect(color_util.color_RGB_to_hsv(0, 0, 255)).to_equal((240, 100, 100))

    expect(color_util.color_RGB_to_hsv(0, 255, 0)).to_equal((120, 100, 100))

    expect(color_util.color_RGB_to_hsv(255, 0, 0)).to_equal((0, 100, 100))


@test
def color_hsv_to_RGB() -> None:
    """Test color_hsv_to_RGB."""
    expect(color_util.color_hsv_to_RGB(0, 0, 0)).to_equal((0, 0, 0))

    expect(color_util.color_hsv_to_RGB(0, 0, 100)).to_equal((255, 255, 255))

    expect(color_util.color_hsv_to_RGB(240, 100, 100)).to_equal((0, 0, 255))

    expect(color_util.color_hsv_to_RGB(120, 100, 100)).to_equal((0, 255, 0))

    expect(color_util.color_hsv_to_RGB(0, 100, 100)).to_equal((255, 0, 0))


@test
def color_hsb_to_RGB() -> None:
    """Test color_hsb_to_RGB."""
    expect(color_util.color_hsb_to_RGB(0, 0, 0)).to_equal((0, 0, 0))

    expect(color_util.color_hsb_to_RGB(0, 0, 1.0)).to_equal((255, 255, 255))

    expect(color_util.color_hsb_to_RGB(240, 1.0, 1.0)).to_equal((0, 0, 255))

    expect(color_util.color_hsb_to_RGB(120, 1.0, 1.0)).to_equal((0, 255, 0))

    expect(color_util.color_hsb_to_RGB(0, 1.0, 1.0)).to_equal((255, 0, 0))


@test
def color_xy_to_hs() -> None:
    """Test color_xy_to_hs."""
    expect(color_util.color_xy_to_hs(1, 1)).to_equal((47.294, 100))

    expect(color_util.color_xy_to_hs(0.35, 0.35)).to_equal((38.182, 12.941))

    expect(color_util.color_xy_to_hs(1, 0)).to_equal((345.882, 100))

    expect(color_util.color_xy_to_hs(0, 1)).to_equal((120, 100))

    expect(color_util.color_xy_to_hs(0, 0)).to_equal((225.176, 100))

    expect(color_util.color_xy_to_hs(1, 0, GAMUT)).to_equal((359.294, 100))

    expect(color_util.color_xy_to_hs(0, 1, GAMUT)).to_equal((100.706, 100))

    expect(color_util.color_xy_to_hs(0, 0, GAMUT)).to_equal((221.463, 96.471))


@test
def color_hs_to_xy() -> None:
    """Test color_hs_to_xy."""
    expect(color_util.color_hs_to_xy(180, 100)).to_equal((0.151, 0.343))

    expect(color_util.color_hs_to_xy(350, 12.5)).to_equal((0.356, 0.321))

    expect(color_util.color_hs_to_xy(140, 50)).to_equal((0.23, 0.474))

    expect(color_util.color_hs_to_xy(0, 40)).to_equal((0.474, 0.317))

    expect(color_util.color_hs_to_xy(360, 0)).to_equal((0.323, 0.329))

    expect(color_util.color_hs_to_xy(0, 100, GAMUT)).to_equal((0.7, 0.299))

    expect(color_util.color_hs_to_xy(120, 100, GAMUT)).to_equal((0.215, 0.711))

    expect(color_util.color_hs_to_xy(180, 100, GAMUT)).to_equal((0.17, 0.34))

    expect(color_util.color_hs_to_xy(240, 100, GAMUT)).to_equal((0.138, 0.08))

    expect(color_util.color_hs_to_xy(360, 100, GAMUT)).to_equal((0.7, 0.299))


@test
def rgb_hex_to_rgb_list() -> None:
    """Test rgb_hex_to_rgb_list."""
    expect(color_util.rgb_hex_to_rgb_list("ffffff")).to_equal([255, 255, 255])

    expect(color_util.rgb_hex_to_rgb_list("000000")).to_equal([0, 0, 0])

    expect(color_util.rgb_hex_to_rgb_list("ffffffff")).to_equal([255, 255, 255, 255])

    expect(color_util.rgb_hex_to_rgb_list("00000000")).to_equal([0, 0, 0, 0])

    expect(color_util.rgb_hex_to_rgb_list("3399ff")).to_equal([51, 153, 255])

    expect(color_util.rgb_hex_to_rgb_list("3399ff00")).to_equal([51, 153, 255, 0])


@test
def color_name_to_rgb_valid_name() -> None:
    """Test color_name_to_rgb."""
    expect(color_util.color_name_to_rgb("red")).to_equal((255, 0, 0))

    expect(color_util.color_name_to_rgb("blue")).to_equal((0, 0, 255))

    expect(color_util.color_name_to_rgb("green")).to_equal((0, 128, 0))

    # Spaces in the name.
    expect(color_util.color_name_to_rgb("dark slate blue")).to_equal((72, 61, 139))

    # Spaces removed from name.
    expect(color_util.color_name_to_rgb("darkslateblue")).to_equal((72, 61, 139))
    expect(color_util.color_name_to_rgb("dark slateblue")).to_equal((72, 61, 139))
    expect(color_util.color_name_to_rgb("darkslate blue")).to_equal((72, 61, 139))


@test
def color_name_to_rgb_unknown_name_raises_value_error() -> None:
    """Test color_name_to_rgb."""
    expect(lambda: color_util.color_name_to_rgb("not a color")).to_raise(ValueError)


@test
def color_rgb_to_rgbw() -> None:
    """Test color_rgb_to_rgbw."""
    expect(color_util.color_rgb_to_rgbw(0, 0, 0)).to_equal((0, 0, 0, 0))

    expect(color_util.color_rgb_to_rgbw(255, 255, 255)).to_equal((0, 0, 0, 255))

    expect(color_util.color_rgb_to_rgbw(255, 0, 0)).to_equal((255, 0, 0, 0))

    expect(color_util.color_rgb_to_rgbw(0, 255, 0)).to_equal((0, 255, 0, 0))

    expect(color_util.color_rgb_to_rgbw(0, 0, 255)).to_equal((0, 0, 255, 0))

    expect(color_util.color_rgb_to_rgbw(255, 127, 0)).to_equal((255, 127, 0, 0))

    expect(color_util.color_rgb_to_rgbw(255, 127, 127)).to_equal((255, 0, 0, 253))

    expect(color_util.color_rgb_to_rgbw(127, 127, 127)).to_equal((0, 0, 0, 127))


@test
def color_rgbw_to_rgb() -> None:
    """Test color_rgbw_to_rgb."""
    expect(color_util.color_rgbw_to_rgb(0, 0, 0, 0)).to_equal((0, 0, 0))

    expect(color_util.color_rgbw_to_rgb(0, 0, 0, 255)).to_equal((255, 255, 255))

    expect(color_util.color_rgbw_to_rgb(255, 0, 0, 0)).to_equal((255, 0, 0))

    expect(color_util.color_rgbw_to_rgb(0, 255, 0, 0)).to_equal((0, 255, 0))

    expect(color_util.color_rgbw_to_rgb(0, 0, 255, 0)).to_equal((0, 0, 255))

    expect(color_util.color_rgbw_to_rgb(255, 127, 0, 0)).to_equal((255, 127, 0))

    expect(color_util.color_rgbw_to_rgb(255, 0, 0, 253)).to_equal((255, 127, 127))

    expect(color_util.color_rgbw_to_rgb(0, 0, 0, 127)).to_equal((127, 127, 127))


@test
def color_xy_to_temperature() -> None:
    """Test color_xy_to_temperature."""
    expect(color_util.color_xy_to_temperature(0.5119, 0.4147)).to_equal(2136)
    expect(color_util.color_xy_to_temperature(0.368, 0.3686)).to_equal(4302)
    expect(color_util.color_xy_to_temperature(0.4448, 0.4066)).to_equal(2893)
    expect(color_util.color_xy_to_temperature(0.1, 0.8)).to_equal(8645)
    expect(color_util.color_xy_to_temperature(0.5, 0.4)).to_equal(2140)


@test
def color_rgb_to_hex() -> None:
    """Test color_rgb_to_hex."""
    expect(color_util.color_rgb_to_hex(255, 255, 255)).to_equal("ffffff")
    expect(color_util.color_rgb_to_hex(0, 0, 0)).to_equal("000000")
    expect(color_util.color_rgb_to_hex(51, 153, 255)).to_equal("3399ff")
    expect(color_util.color_rgb_to_hex(255, 67.9204190, 0)).to_equal("ff4400")


@test
def match_max_scale() -> None:
    """Test match_max_scale."""
    match_max_scale = color_util.match_max_scale
    expect(match_max_scale((255, 255, 255), (255, 255, 255))).to_equal((255, 255, 255))
    expect(match_max_scale((0, 0, 0), (0, 0, 0))).to_equal((0, 0, 0))
    expect(match_max_scale((255, 255, 255), (128, 128, 128))).to_equal((255, 255, 255))
    expect(match_max_scale((0, 255, 0), (64, 128, 128))).to_equal((128, 255, 255))
    expect(match_max_scale((0, 100, 0), (128, 64, 64))).to_equal((100, 50, 50))
    expect(match_max_scale((10, 20, 33), (100, 200, 333))).to_equal((10, 20, 33))
    expect(match_max_scale((255,), (100, 200, 333))).to_equal((77, 153, 255))
    expect(match_max_scale((128,), (10.5, 20.9, 30.4))).to_equal((44, 88, 128))
    expect(match_max_scale((10, 20, 30, 128), (100, 200, 333))).to_equal((38, 77, 128))


@test
def gamut() -> None:
    """Test gamut functions."""
    expect(color_util.check_valid_gamut(GAMUT)).to_be_truthy()
    expect(color_util.check_valid_gamut(GAMUT_INVALID_1)).to_be_falsy()
    expect(color_util.check_valid_gamut(GAMUT_INVALID_2)).to_be_falsy()
    expect(color_util.check_valid_gamut(GAMUT_INVALID_3)).to_be_falsy()
    expect(color_util.check_valid_gamut(GAMUT_INVALID_4)).to_be_falsy()


@test
def color_temperature_mired_to_kelvin() -> None:
    """Test color_temperature_mired_to_kelvin."""
    expect(color_util.color_temperature_mired_to_kelvin(40)).to_equal(25000)
    expect(color_util.color_temperature_mired_to_kelvin(200)).to_equal(5000)
    expect(lambda: color_util.color_temperature_mired_to_kelvin(0)).to_raise(
        ZeroDivisionError
    )


@test
def color_temperature_kelvin_to_mired() -> None:
    """Test color_temperature_kelvin_to_mired."""
    expect(color_util.color_temperature_kelvin_to_mired(25000)).to_equal(40)
    expect(color_util.color_temperature_kelvin_to_mired(5000)).to_equal(200)
    expect(lambda: color_util.color_temperature_kelvin_to_mired(0)).to_raise(
        ZeroDivisionError
    )


@test
def returns_same_value_for_any_two_temperatures_below_1000() -> None:
    """Function should return same value for 999 Kelvin and 0 Kelvin."""
    rgb_1 = color_util.color_temperature_to_rgb(999)
    rgb_2 = color_util.color_temperature_to_rgb(0)
    expect(rgb_1).to_equal(rgb_2)


@test
def returns_same_value_for_any_two_temperatures_above_40000() -> None:
    """Function should return same value for 40001K and 999999K."""
    rgb_1 = color_util.color_temperature_to_rgb(40001)
    rgb_2 = color_util.color_temperature_to_rgb(999999)
    expect(rgb_1).to_equal(rgb_2)


@test
def should_return_pure_white_at_6600() -> None:
    """Function should return red=255, blue=255, green=255 when given 6600K.

    6600K is considered "pure white" light.
    This is just a rough estimate because the formula itself is a "best
    guess" approach.
    """
    rgb = color_util.color_temperature_to_rgb(6600)
    expect(rgb).to_equal((255, 255, 255))


@test
def color_above_6600_should_have_more_blue_than_red_or_green() -> None:
    """Function should return a higher blue value for blue-ish light."""
    rgb = color_util.color_temperature_to_rgb(6700)
    expect(rgb[2] > rgb[1]).to_be(True)
    expect(rgb[2] > rgb[0]).to_be(True)


@test
def color_below_6600_should_have_more_red_than_blue_or_green() -> None:
    """Function should return a higher red value for red-ish light."""
    rgb = color_util.color_temperature_to_rgb(6500)
    expect(rgb[0] > rgb[1]).to_be(True)
    expect(rgb[0] > rgb[2]).to_be(True)


@test
def get_color_in_voluptuous() -> None:
    """Test using the get method in color validation."""
    schema = vol.Schema(color_util.color_name_to_rgb)

    expect(lambda: schema("not a color")).to_raise(vol.Invalid)

    expect(schema("red")).to_equal((255, 0, 0))


@test
def color_rgb_to_rgbww() -> None:
    """Test color_rgb_to_rgbww conversions."""
    # Light with mid point at ~4600K (warm white) -> output compensated by adding blue.
    expect(color_util.color_rgb_to_rgbww(255, 255, 255, 2702, 6493)).to_equal(
        (0, 54, 98, 255, 255)
    )
    # Light with mid point at ~5500K (less warm white) -> output compensated by adding less blue.
    expect(color_util.color_rgb_to_rgbww(255, 255, 255, 1000, 10000)).to_equal(
        (255, 255, 255, 0, 0)
    )
    # Light with mid point at ~1MK (unrealistically cold white) -> output compensated by adding red.
    expect(color_util.color_rgb_to_rgbww(255, 255, 255, 1000, 1000000)).to_equal(
        (0, 118, 241, 255, 255)
    )
    expect(color_util.color_rgb_to_rgbww(128, 128, 128, 2702, 6493)).to_equal(
        (0, 27, 49, 128, 128)
    )
    expect(color_util.color_rgb_to_rgbww(64, 64, 64, 2702, 6493)).to_equal(
        (0, 14, 25, 64, 64)
    )
    expect(color_util.color_rgb_to_rgbww(32, 64, 16, 2702, 6493)).to_equal(
        (9, 64, 0, 38, 38)
    )
    expect(color_util.color_rgb_to_rgbww(0, 0, 0, 2702, 6493)).to_equal((0, 0, 0, 0, 0))
    expect(color_util.color_rgb_to_rgbww(0, 0, 0, 10000, 1000000)).to_equal(
        (0, 0, 0, 0, 0)
    )
    expect(color_util.color_rgb_to_rgbww(255, 255, 255, 200000, 1000000)).to_equal(
        (103, 69, 0, 255, 255)
    )


@test
def color_rgbww_to_rgb() -> None:
    """Test color_rgbww_to_rgb conversions."""
    expect(color_util.color_rgbww_to_rgb(0, 54, 98, 255, 255, 2702, 6493)).to_equal(
        (255, 255, 255)
    )
    # rgb fully on, + both white channels turned off -> rgb fully on.
    expect(color_util.color_rgbww_to_rgb(255, 255, 255, 0, 0, 2702, 6493)).to_equal(
        (255, 255, 255)
    )
    # r < g < b + both white channels fully enabled -> r < g < b capped at 255.
    expect(color_util.color_rgbww_to_rgb(0, 118, 241, 255, 255, 2702, 6493)).to_equal(
        (163, 204, 255)
    )
    # r < g < b + both white channels 50% enabled -> r < g < b capped at 128.
    expect(color_util.color_rgbww_to_rgb(0, 27, 49, 128, 128, 2702, 6493)).to_equal(
        (128, 128, 128)
    )
    # r < g < b + both white channels 25% enabled -> r < g < b capped at 64.
    expect(color_util.color_rgbww_to_rgb(0, 14, 25, 64, 64, 2702, 6493)).to_equal(
        (64, 64, 64)
    )
    expect(color_util.color_rgbww_to_rgb(9, 64, 0, 38, 38, 2702, 6493)).to_equal(
        (32, 64, 16)
    )
    expect(color_util.color_rgbww_to_rgb(0, 0, 0, 0, 0, 2702, 6493)).to_equal((0, 0, 0))
    expect(color_util.color_rgbww_to_rgb(103, 69, 0, 255, 255, 2702, 6535)).to_equal(
        (255, 193, 112)
    )


@test
def color_temperature_to_rgbww() -> None:
    """Test color temp to warm, cold conversion.

    Temperature values must be in mireds.
    Home Assistant uses rgbcw for rgbww.
    """
    # Coldest color temperature -> only cold channel enabled.
    expect(color_util.color_temperature_to_rgbww(6535, 255, 2000, 6535)).to_equal(
        (0, 0, 0, 255, 0)
    )
    expect(color_util.color_temperature_to_rgbww(6535, 128, 2000, 6535)).to_equal(
        (0, 0, 0, 128, 0)
    )
    # Warmest color temperature -> only cold channel enabled.
    expect(color_util.color_temperature_to_rgbww(2000, 255, 2000, 6535)).to_equal(
        (0, 0, 0, 0, 255)
    )
    expect(color_util.color_temperature_to_rgbww(2000, 128, 2000, 6535)).to_equal(
        (0, 0, 0, 0, 128)
    )
    # Warmer than mid point color temperature -> More warm than cold channel enabled.
    expect(color_util.color_temperature_to_rgbww(2881, 255, 2000, 6535)).to_equal(
        (0, 0, 0, 112, 143)
    )
    expect(color_util.color_temperature_to_rgbww(2881, 128, 2000, 6535)).to_equal(
        (0, 0, 0, 56, 72)
    )


@test
def rgbww_to_color_temperature() -> None:
    """Test rgbww conversion to color temp.

    Temperature values must be in mireds.
    Home Assistant uses rgbcw for rgbww.
    """
    # Only cold channel enabled -> coldest color temperature.
    expect(
        color_util.rgbww_to_color_temperature((0, 0, 0, 255, 0), 2000, 6535)
    ).to_equal((6535, 255))
    expect(
        color_util.rgbww_to_color_temperature((0, 0, 0, 128, 0), 2000, 6535)
    ).to_equal((6535, 128))
    # Only warm channel enabled -> warmest color temperature.
    expect(
        color_util.rgbww_to_color_temperature((0, 0, 0, 0, 255), 2000, 6535)
    ).to_equal((2000, 255))
    expect(
        color_util.rgbww_to_color_temperature((0, 0, 0, 0, 128), 2000, 6535)
    ).to_equal((2000, 128))
    # More warm than cold channel enabled -> warmer than mid point.
    expect(
        color_util.rgbww_to_color_temperature((0, 0, 0, 112, 143), 2000, 6535)
    ).to_equal((2876, 255))
    expect(
        color_util.rgbww_to_color_temperature((0, 0, 0, 56, 72), 2000, 6535)
    ).to_equal((2872, 128))
    # Both channels turned off -> warmest color temperature.
    expect(color_util.rgbww_to_color_temperature((0, 0, 0, 0, 0), 2000, 6535)).to_equal(
        (2000, 0)
    )


@test
def white_levels_to_color_temperature() -> None:
    """Test warm, cold conversion to color temp.

    Temperature values must be in mireds.
    Home Assistant uses rgbcw for rgbww.
    """
    # Only cold channel enabled -> coldest color temperature.
    expect(color_util._white_levels_to_color_temperature(255, 0, 2000, 6535)).to_equal(
        (6535, 255)
    )
    expect(color_util._white_levels_to_color_temperature(128, 0, 2000, 6535)).to_equal(
        (6535, 128)
    )
    # Only warm channel enabled -> warmest color temperature.
    expect(color_util._white_levels_to_color_temperature(0, 255, 2000, 6535)).to_equal(
        (2000, 255)
    )
    expect(color_util._white_levels_to_color_temperature(0, 128, 2000, 6535)).to_equal(
        (2000, 128)
    )
    expect(
        color_util._white_levels_to_color_temperature(112, 143, 2000, 6535)
    ).to_equal((2876, 255))
    expect(color_util._white_levels_to_color_temperature(56, 72, 2000, 6535)).to_equal(
        (2872, 128)
    )
    # Both channels turned off -> warmest color temperature.
    expect(color_util._white_levels_to_color_temperature(0, 0, 2000, 6535)).to_equal(
        (2000, 0)
    )


@test.cases(
    test.case("530-255", value=530, brightness=255),  # Test min==255 clamp.
    test.case("511-255", value=511, brightness=255),
    test.case("255-127", value=255, brightness=127),
    test.case("49-24", value=49, brightness=24),
    test.case("1-1", value=1, brightness=1),
    test.case("0-1", value=0, brightness=1),  # Test max==1 clamp.
)
async def ranged_value_to_brightness_large(value: float, brightness: int) -> None:
    """Test a large scale and clamping and convert a single value to a brightness."""
    scale = (1, 511)

    expect(color_util.value_to_brightness(scale, value)).to_equal(brightness)


@test.cases(
    test.case("255-511-511", brightness=255, value=511.0, math_ceil=511),
    test.case(
        "127-254.498-255", brightness=127, value=254.49803921568628, math_ceil=255
    ),
    test.case("24-48.094-49", brightness=24, value=48.09411764705882, math_ceil=49),
)
async def brightness_to_ranged_value_large(
    brightness: int, value: float, math_ceil: int
) -> None:
    """Test a large scale and convert a brightness to a single value."""
    scale = (1, 511)

    expect(color_util.brightness_to_value(scale, brightness)).to_equal(value)

    expect(math.ceil(color_util.brightness_to_value(scale, brightness))).to_equal(
        math_ceil
    )


@test.cases(
    test.case("1-4-1-64", scale=(1, 4), value=1, brightness=64),
    test.case("1-4-2-128", scale=(1, 4), value=2, brightness=128),
    test.case("1-4-3-191", scale=(1, 4), value=3, brightness=191),
    test.case("1-4-4-255", scale=(1, 4), value=4, brightness=255),
    test.case("1-6-1-42", scale=(1, 6), value=1, brightness=42),
    test.case("1-6-2-85", scale=(1, 6), value=2, brightness=85),
    test.case("1-6-3-128", scale=(1, 6), value=3, brightness=128),
    test.case("1-6-4-170", scale=(1, 6), value=4, brightness=170),
    test.case("1-6-5-212", scale=(1, 6), value=5, brightness=212),
    test.case("1-6-6-255", scale=(1, 6), value=6, brightness=255),
)
async def ranged_value_to_brightness_small(
    scale: tuple[float, float], value: float, brightness: int
) -> None:
    """Test a small scale and convert a single value to a brightness."""
    expect(color_util.value_to_brightness(scale, value)).to_equal(brightness)


@test.cases(
    test.case("1-4-63-1", scale=(1, 4), brightness=63, value=1),
    test.case("1-4-127-2", scale=(1, 4), brightness=127, value=2),
    test.case("1-4-191-3", scale=(1, 4), brightness=191, value=3),
    test.case("1-4-255-4", scale=(1, 4), brightness=255, value=4),
    test.case("1-6-42-1", scale=(1, 6), brightness=42, value=1),
    test.case("1-6-85-2", scale=(1, 6), brightness=85, value=2),
    test.case("1-6-127-3", scale=(1, 6), brightness=127, value=3),
    test.case("1-6-170-4", scale=(1, 6), brightness=170, value=4),
    test.case("1-6-212-5", scale=(1, 6), brightness=212, value=5),
    test.case("1-6-255-6", scale=(1, 6), brightness=255, value=6),
)
async def brightness_to_ranged_value_small(
    scale: tuple[float, float], brightness: int, value: float
) -> None:
    """Test a small scale and convert a brightness to a single value."""
    expect(math.ceil(color_util.brightness_to_value(scale, brightness))).to_equal(value)


@test.cases(
    test.case("101-2", value=101, brightness=2),
    test.case("139-64", value=139, brightness=64),
    test.case("178-128", value=178, brightness=128),
    test.case("217-192", value=217, brightness=192),
    test.case("255-255", value=255, brightness=255),
)
async def ranged_value_to_brightness_starting_high(
    value: float, brightness: int
) -> None:
    """Test a range that does not start with 1."""
    scale = (101, 255)

    expect(color_util.value_to_brightness(scale, value)).to_equal(brightness)


@test.cases(
    test.case("0-64", value=0, brightness=64),
    test.case("1-128", value=1, brightness=128),
    test.case("2-191", value=2, brightness=191),
    test.case("3-255", value=3, brightness=255),
)
async def ranged_value_to_brightness_starting_zero(
    value: float, brightness: int
) -> None:
    """Test a range that starts with 0."""
    scale = (0, 3)

    expect(color_util.value_to_brightness(scale, value)).to_equal(brightness)


@test.skip(reason="syrupy snapshot testing not supported by Tryke")
async def brightness_to_254_range() -> None:
    """Test brightness scaling to a 254 range and back."""
