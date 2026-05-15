"""Test the Light significant change platform."""

from tryke import expect, test

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ATTR_HS_COLOR,
)
from homeassistant.components.light.significant_change import (
    async_check_significant_change,
)


@test
async def significant_change() -> None:
    """Detect Light significant changes."""
    expect(async_check_significant_change(None, "on", {}, "on", {})).to_be(False)
    expect(async_check_significant_change(None, "on", {}, "off", {})).to_be(True)

    # Brightness
    expect(
        async_check_significant_change(
            None, "on", {ATTR_BRIGHTNESS: 60}, "on", {ATTR_BRIGHTNESS: 61}
        )
    ).to_be(False)
    expect(
        async_check_significant_change(
            None, "on", {ATTR_BRIGHTNESS: 60}, "on", {ATTR_BRIGHTNESS: 63}
        )
    ).to_be(True)

    # Color temp
    expect(
        async_check_significant_change(
            None,
            "on",
            {ATTR_COLOR_TEMP_KELVIN: 2000},
            "on",
            {ATTR_COLOR_TEMP_KELVIN: 2049},
        )
    ).to_be(False)
    expect(
        async_check_significant_change(
            None,
            "on",
            {ATTR_COLOR_TEMP_KELVIN: 2000},
            "on",
            {ATTR_COLOR_TEMP_KELVIN: 2050},
        )
    ).to_be(True)

    # Effect
    for eff1, eff2, expected in (
        (None, None, False),
        (None, "colorloop", True),
        ("colorloop", None, True),
        ("colorloop", "jump", True),
        ("colorloop", "colorloop", False),
    ):
        result = async_check_significant_change(
            None, "on", {ATTR_EFFECT: eff1}, "on", {ATTR_EFFECT: eff2}
        )
        expect(result is expected).to_be(True)

    # Hue
    expect(
        async_check_significant_change(
            None, "on", {ATTR_HS_COLOR: [120, 20]}, "on", {ATTR_HS_COLOR: [124, 20]}
        )
    ).to_be(False)
    expect(
        async_check_significant_change(
            None, "on", {ATTR_HS_COLOR: [120, 20]}, "on", {ATTR_HS_COLOR: [125, 20]}
        )
    ).to_be(True)

    # Saturation
    expect(
        async_check_significant_change(
            None, "on", {ATTR_HS_COLOR: [120, 20]}, "on", {ATTR_HS_COLOR: [120, 22]}
        )
    ).to_be(False)
    expect(
        async_check_significant_change(
            None, "on", {ATTR_HS_COLOR: [120, 20]}, "on", {ATTR_HS_COLOR: [120, 23]}
        )
    ).to_be(True)
