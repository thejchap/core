"""Test service_info helpers."""

from typing import Any

from tryke import expect, test

from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from homeassistant.helpers.service_info.esphome import ESPHomeServiceInfo

# The canonical pytest tests/conftest.py wraps DhcpServiceInfo.__init__
# so that unformatted MAC addresses raise ValueError. Under Tryke there
# is no conftest equivalent, so reapply the patch here at import time.
_real_dhcp_service_info_init = DhcpServiceInfo.__init__


def _dhcp_service_info_init(self: DhcpServiceInfo, *args: Any, **kwargs: Any) -> None:
    _real_dhcp_service_info_init(self, *args, **kwargs)
    if self.macaddress != self.macaddress.lower().replace(":", ""):
        raise ValueError("macaddress is not correctly formatted")


DhcpServiceInfo.__init__ = _dhcp_service_info_init

# Ensure that incorrectly formatted mac addresses are rejected, even
# on a constant outside of a test.
try:
    _ = DhcpServiceInfo(ip="", hostname="", macaddress="AA:BB:CC:DD:EE:FF")
except ValueError:
    pass
else:
    raise RuntimeError(
        "DhcpServiceInfo incorrectly formatted mac address was not rejected. "
        "Please ensure that the DhcpServiceInfo is correctly patched."
    )


@test
def invalid_macaddress() -> None:
    """Test that DhcpServiceInfo raises ValueError for unformatted macaddress."""
    expect(
        lambda: DhcpServiceInfo(ip="", hostname="", macaddress="AA:BB:CC:DD:EE:FF")
    ).to_raise(ValueError)


@test
def esphome_socket_path() -> None:
    """Test ESPHomeServiceInfo socket_path property."""
    info = ESPHomeServiceInfo(
        name="Hello World",
        zwave_home_id=123456789,
        ip_address="192.168.1.100",
        port=6053,
    )
    expect(info.socket_path).to_equal("esphome://192.168.1.100:6053")
    info.noise_psk = "my-noise-psk"
    expect(info.socket_path).to_equal("esphome://192.168.1.100:6053/?key=my-noise-psk")
