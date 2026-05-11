"""Tests for Broadlink helper functions."""

import voluptuous as vol
from tryke import expect, test

from homeassistant.components.broadlink.helpers import data_packet, mac_address


@test
def padding() -> None:
    """Verify that non padding strings are allowed."""
    expect(data_packet("Jg")).to_equal(b"&")
    expect(data_packet("Jg=")).to_equal(b"&")
    expect(data_packet("Jg==")).to_equal(b"&")


@test
def valid_mac_address() -> None:
    """Test we convert a valid MAC address to bytes."""
    valid = [
        "A1B2C3D4E5F6",
        "a1b2c3d4e5f6",
        "A1B2-C3D4-E5F6",
        "a1b2-c3d4-e5f6",
        "A1B2.C3D4.E5F6",
        "a1b2.c3d4.e5f6",
        "A1-B2-C3-D4-E5-F6",
        "a1-b2-c3-d4-e5-f6",
        "A1:B2:C3:D4:E5:F6",
        "a1:b2:c3:d4:e5:f6",
    ]
    for mac in valid:
        expect(mac_address(mac)).to_equal(b"\xa1\xb2\xc3\xd4\xe5\xf6")


@test
def invalid_mac_address() -> None:
    """Test we do not accept an invalid MAC address."""
    invalid = [
        None,
        123,
        ["a", "b", "c"],
        {"abc": "def"},
        "a1b2c3d4e5f",
        "a1b2.c3d4.e5f",
        "a1-b2-c3-d4-e5-f",
        "a1b2c3d4e5f66",
        "a1b2.c3d4.e5f66",
        "a1-b2-c3-d4-e5-f66",
        "a1b2c3d4e5fg",
        "a1b2.c3d4.e5fg",
        "a1-b2-c3-d4-e5-fg",
        "a1b.2c3d4.e5fg",
        "a1b-2-c3-d4-e5-fg",
    ]
    for mac in invalid:
        raised = False
        try:
            mac_address(mac)
        except (ValueError, vol.Invalid):
            raised = True
        expect(raised).to_be(True)
