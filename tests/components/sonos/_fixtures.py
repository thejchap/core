"""Tryke fixtures for the Sonos integration."""

from ipaddress import ip_address

from tryke import fixture

from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo


@fixture
def zeroconf_payload() -> ZeroconfServiceInfo:
    """Return a default zeroconf payload."""
    return ZeroconfServiceInfo(
        ip_address=ip_address("192.168.4.2"),
        ip_addresses=[ip_address("192.168.4.2")],
        hostname="Sonos-aaa",
        name="Sonos-aaa@Living Room._sonos._tcp.local.",
        port=None,
        properties={"bootseq": "1234"},
        type="mock_type",
    )
