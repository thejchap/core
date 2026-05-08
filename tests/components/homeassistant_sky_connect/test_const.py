"""Test the Home Assistant SkyConnect constants."""

from tryke import expect, test

from homeassistant.components.homeassistant_sky_connect.const import HardwareVariant


@test.cases(
    test.case(
        "skyconnect",
        usb_product_name="SkyConnect v1.0",
        expected_variant=HardwareVariant.SKYCONNECT,
    ),
    test.case(
        "connect_zbt1",
        usb_product_name="Home Assistant Connect ZBT-1",
        expected_variant=HardwareVariant.CONNECT_ZBT1,
    ),
)
def hardware_variant(
    *, usb_product_name: str, expected_variant: HardwareVariant
) -> None:
    """Test hardware variant parsing."""
    expect(HardwareVariant.from_usb_product_name(usb_product_name)).to_equal(
        expected_variant
    )


@test
def hardware_variant_invalid() -> None:
    """Test hardware variant parsing with an invalid product."""
    expect(
        lambda: HardwareVariant.from_usb_product_name("Some other product")
    ).to_raise(ValueError, match=r"^Unknown SkyConnect product name: Some other product$")
