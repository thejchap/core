"""Tryke fixtures for D-Link."""

from collections.abc import Generator
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture

from homeassistant.components.dlink.const import CONF_USE_LEGACY_PROTOCOL, DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass

HOST = "1.2.3.4"
PASSWORD = "123456"
MAC = format_mac("AA:BB:CC:DD:EE:FF")
DHCP_FORMATTED_MAC = MAC.replace(":", "")
USERNAME = "admin"

CONF_DHCP_DATA = {
    CONF_USERNAME: USERNAME,
    CONF_PASSWORD: PASSWORD,
    CONF_USE_LEGACY_PROTOCOL: True,
}

CONF_DATA = CONF_DHCP_DATA | {CONF_HOST: HOST}

CONF_DHCP_FLOW = DhcpServiceInfo(
    ip=HOST,
    macaddress=DHCP_FORMATTED_MAC,
    hostname="dsp-w215",
)

CONF_DHCP_FLOW_NEW_IP = DhcpServiceInfo(
    ip="5.6.7.8",
    macaddress=DHCP_FORMATTED_MAC,
    hostname="dsp-w215",
)


def patch_config_flow(mocked_plug: MagicMock):
    """Patch D-Link Smart Plug config flow."""
    return patch(
        "homeassistant.components.dlink.config_flow.SmartPlug",
        return_value=mocked_plug,
    )


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass),
) -> MockConfigEntry:
    """Add config entry in Home Assistant."""
    entry = MockConfigEntry(domain=DOMAIN, data=CONF_DATA, unique_id=None)
    entry.add_to_hass(hass)
    return entry


@fixture
def config_entry_with_uid(
    hass: HomeAssistant = Depends(hass),
) -> MockConfigEntry:
    """Add config entry with unique ID in Home Assistant."""
    entry = MockConfigEntry(domain=DOMAIN, data=CONF_DATA, unique_id="aabbccddeeff")
    entry.add_to_hass(hass)
    return entry


@fixture
def mocked_plug() -> MagicMock:
    """Create mocked plug device."""
    mocked_plug = MagicMock()
    mocked_plug.state = "OFF"
    mocked_plug.temperature = "33"
    mocked_plug.current_consumption = "50"
    mocked_plug.total_consumption = "1040"
    mocked_plug.authenticated = None
    mocked_plug.use_legacy_protocol = False
    mocked_plug.model_name = "DSP-W215"
    return mocked_plug


@fixture
def mocked_plug_legacy() -> MagicMock:
    """Create mocked legacy plug device."""
    mocked_plug = MagicMock()
    mocked_plug.state = "OFF"
    mocked_plug.temperature = "N/A"
    mocked_plug.current_consumption = "N/A"
    mocked_plug.total_consumption = "N/A"
    mocked_plug.authenticated = ("0123456789ABCDEF0123456789ABCDEF", "ABCDefGHiJ")
    mocked_plug.use_legacy_protocol = True
    mocked_plug.model_name = "DSP-W215"
    return mocked_plug


@fixture
def mocked_plug_legacy_no_auth(
    mocked_plug_legacy: MagicMock = Depends(mocked_plug_legacy),
) -> MagicMock:
    """Create mocked legacy unauthenticated plug device."""
    legacy = deepcopy(mocked_plug_legacy)
    legacy.authenticated = None
    return legacy


@fixture
def mock_zeroconf() -> Generator[MagicMock]:
    """Mock zeroconf."""
    from zeroconf import DNSCache  # noqa: PLC0415

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch(
            "homeassistant.components.zeroconf.discovery.AsyncServiceBrowser",
        ) as mock_browser,
    ):
        asb = mock_browser.return_value
        asb.async_cancel = AsyncMock()
        zc = mock_zc.return_value
        zc.cache = DNSCache()
        yield mock_zc
