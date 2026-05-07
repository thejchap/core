"""Test the sonos config flow."""

from ipaddress import ip_address
from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.media_player import DOMAIN as MP_DOMAIN
from homeassistant.components.sonos.const import DATA_SONOS_DISCOVERY_MANAGER, DOMAIN
from homeassistant.const import CONF_HOSTS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from homeassistant.setup import async_setup_component

from ._fixtures import zeroconf_payload

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture for fixture resolution."""


@test
async def user_form(
    _trigger: None = Depends(_trigger_executor),
    payload: ZeroconfServiceInfo = Depends(zeroconf_payload),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the user initiated form."""
    # Ensure config flow will fail if no devices discovered yet
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")

    # Initiate a discovery to allow config entry creation
    await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=payload,
    )

    # Ensure config flow succeeds after discovery
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)
    with (
        patch(
            "homeassistant.components.sonos.async_setup",
            return_value=True,
        ) as mock_setup,
        patch(
            "homeassistant.components.sonos.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Sonos")
    expect(result2["data"]).to_equal({})
    expect(len(mock_setup.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_form_already_created(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure we abort a flow if the entry is already created from config."""
    config = {DOMAIN: {MP_DOMAIN: {CONF_HOSTS: "192.168.4.2"}}}
    with patch(
        "homeassistant.components.sonos.async_setup_entry",
        return_value=True,
    ):
        await async_setup_component(hass, DOMAIN, config)
        await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def zeroconf_form(
    _trigger: None = Depends(_trigger_executor),
    payload: ZeroconfServiceInfo = Depends(zeroconf_payload),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we pass Zeroconf discoveries to the manager."""
    mock_manager = hass.data[DATA_SONOS_DISCOVERY_MANAGER] = MagicMock()
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=payload,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch(
            "homeassistant.components.sonos.async_setup",
            return_value=True,
        ) as mock_setup,
        patch(
            "homeassistant.components.sonos.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Sonos")
    expect(result2["data"]).to_equal({})

    expect(len(mock_setup.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_manager.mock_calls)).to_equal(2)


@test
async def zeroconf_form_not_ipv4(
    _trigger: None = Depends(_trigger_executor),
    payload: ZeroconfServiceInfo = Depends(zeroconf_payload),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we pass Zeroconf discoveries to the manager."""
    mock_manager = hass.data[DATA_SONOS_DISCOVERY_MANAGER] = MagicMock()
    payload.ip_address = ip_address("2001:db8:3333:4444:5555:6666:7777:8888")
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=payload,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_ipv4_address")
    expect(mock_manager.call_count).to_equal(0)


@test
async def zeroconf_sonos_v1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we pass sonos devices to the discovery manager with v1 firmware devices."""
    mock_manager = hass.data[DATA_SONOS_DISCOVERY_MANAGER] = MagicMock()
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.107"),
            ip_addresses=[ip_address("192.168.1.107")],
            port=1443,
            hostname="sonos5CAAFDE47AC8.local.",
            type="_sonos._tcp.local.",
            name="Sonos-5CAAFDE47AC8._sonos._tcp.local.",
            properties={
                "_raw": {
                    "info": b"/api/v1/players/RINCON_5CAAFDE47AC801400/info",
                    "vers": b"1",
                    "protovers": b"1.18.9",
                },
                "info": "/api/v1/players/RINCON_5CAAFDE47AC801400/info",
                "vers": "1",
                "protovers": "1.18.9",
            },
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch(
            "homeassistant.components.sonos.async_setup",
            return_value=True,
        ) as mock_setup,
        patch(
            "homeassistant.components.sonos.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Sonos")
    expect(result2["data"]).to_equal({})

    expect(len(mock_setup.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_manager.mock_calls)).to_equal(2)


@test
async def zeroconf_form_not_sonos(
    _trigger: None = Depends(_trigger_executor),
    payload: ZeroconfServiceInfo = Depends(zeroconf_payload),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort on non-sonos devices."""
    mock_manager = hass.data[DATA_SONOS_DISCOVERY_MANAGER] = MagicMock()

    payload.hostname = "not-aaa"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=payload,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_sonos_device")
    expect(len(mock_manager.mock_calls)).to_equal(0)


@test.skip("ssdp_discovery requires soco fixture (complex MockSoCo with many plugins)")
async def ssdp_discovery() -> None:
    """Skipped pending soco fixture port."""
