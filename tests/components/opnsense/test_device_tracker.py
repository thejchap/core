"""The tests for the opnsense device tracker platform."""

from unittest import mock

from tryke import Depends, expect, fixture, test

from homeassistant.components import opnsense
from homeassistant.components.device_tracker import legacy
from homeassistant.components.opnsense import CONF_API_SECRET, DOMAIN
from homeassistant.const import CONF_API_KEY, CONF_URL, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.components.opnsense._fixtures import mock_device_tracker_conf
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def get_scanner(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_device_tracker_conf: list[legacy.Device] = Depends(mock_device_tracker_conf),
) -> None:
    """Test creating an opnsense scanner."""
    with mock.patch.object(opnsense, "OPNsenseClient") as mocked_opnsense:
        opnsense_client = mock.AsyncMock()
        mocked_opnsense.return_value = opnsense_client
        opnsense_client.get_arp_table.return_value = [
            {
                "hostname": "",
                "intf": "igb1",
                "intf_description": "LAN",
                "ip": "192.168.0.123",
                "mac": "ff:ff:ff:ff:ff:ff",
                "manufacturer": "",
            },
            {
                "hostname": "Desktop",
                "intf": "igb1",
                "intf_description": "LAN",
                "ip": "192.168.0.167",
                "mac": "ff:ff:ff:ff:ff:fe",
                "manufacturer": "OEM",
            },
        ]

        opnsense_client.get_interfaces.return_value = {
            "wan": {"name": "WAN"},
            "lan": {"name": "LAN"},
        }

        result = await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    CONF_URL: "https://fake_host_fun/api",
                    CONF_API_KEY: "fake_key",
                    CONF_API_SECRET: "fake_secret",
                    CONF_VERIFY_SSL: False,
                }
            },
        )
        await hass.async_block_till_done()
        expect(result).to_be(True)
        device_1 = hass.states.get("device_tracker.desktop")
        expect(device_1 is not None).to_be(True)
        expect(device_1.state).to_equal("home")
        device_2 = hass.states.get("device_tracker.ff_ff_ff_ff_ff_ff")
        expect(device_2.state).to_equal("home")
