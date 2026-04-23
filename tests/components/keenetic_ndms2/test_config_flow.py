"""Test Keenetic NDMS2 setup process."""

import dataclasses
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from ndms2_client import ConnectionException
from ndms2_client.client import InterfaceInfo, RouterInfo
from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import keenetic_ndms2 as keenetic
from homeassistant.components.keenetic_ndms2 import CONF_INTERFACES, const
from homeassistant.const import CONF_HOST, CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import (
    ATTR_UPNP_FRIENDLY_NAME,
    ATTR_UPNP_UDN,
)

from . import (
    MOCK_DATA,
    MOCK_IP,
    MOCK_NAME,
    MOCK_OPTIONS,
    MOCK_RECONFIGURE,
    MOCK_SSDP_DISCOVERY_INFO,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


_ROUTER_INFO = RouterInfo(
    name=MOCK_NAME,
    fw_version="3.0.4",
    fw_channel="stable",
    model="mock",
    hw_version="0000",
    manufacturer="pytest",
    vendor="foxel",
    region="RU",
)


@fixture
def _mock_zeroconf() -> MagicMock:
    """Patch zeroconf so tests don't require a real zeroconf instance."""
    from zeroconf import DNSCache

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch("homeassistant.components.zeroconf.discovery.AsyncServiceBrowser"),
    ):
        zc = mock_zc.return_value
        zc.async_add_service_listener = AsyncMock()
        zc.async_remove_service_listener = AsyncMock()
        zc.async_register_service = AsyncMock()
        zc.async_update_service = AsyncMock()
        zc.cache = DNSCache()
        yield mock_zc


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mz: MagicMock = Depends(_mock_zeroconf),
) -> None:
    """Trigger the hook executor path."""
    return None


@fixture
def router_info_mock() -> MagicMock:
    """Mock router info callable; default returns a successful RouterInfo."""
    with patch("ndms2_client.client.Client.get_router_info") as mock:
        mock.return_value = _ROUTER_INFO
        yield mock


@test
async def flow_works(
    hass: HomeAssistant = Depends(hass_fixture),
    _router_info_mock: MagicMock = Depends(router_info_mock),
) -> None:
    """Test config flow."""
    result = await hass.config_entries.flow.async_init(
        keenetic.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.keenetic_ndms2.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_DATA
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(MOCK_NAME)
    expect(result2["data"]).to_equal(MOCK_DATA)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def reconfigure(
    hass: HomeAssistant = Depends(hass_fixture),
    _router_info_mock: MagicMock = Depends(router_info_mock),
) -> None:
    """Test reconfigure flow."""
    entry = MockConfigEntry(domain=keenetic.DOMAIN, data=MOCK_DATA)
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.keenetic_ndms2.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_RECONFIGURE
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal({CONF_HOST: MOCK_IP, **MOCK_RECONFIGURE})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def options(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test updating options."""
    entry = MockConfigEntry(domain=keenetic.DOMAIN, data=MOCK_DATA)
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.keenetic_ndms2.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    entry.runtime_data = Mock(
        client=Mock(
            get_interfaces=Mock(
                return_value=[
                    InterfaceInfo.from_dict({"id": name, "type": "bridge"})
                    for name in MOCK_OPTIONS[const.CONF_INTERFACES]
                ]
            )
        )
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=MOCK_OPTIONS
    )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["data"]).to_equal(MOCK_OPTIONS)


@test
async def host_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    _router_info_mock: MagicMock = Depends(router_info_mock),
) -> None:
    """Test host already configured."""
    entry = MockConfigEntry(
        domain=keenetic.DOMAIN, data=MOCK_DATA, options=MOCK_OPTIONS
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        keenetic.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_DATA
    )
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def connection_error(
    hass: HomeAssistant = Depends(hass_fixture),
    router_info_mock: MagicMock = Depends(router_info_mock),
) -> None:
    """Test error when connection is unsuccessful."""
    router_info_mock.side_effect = ConnectionException("Mocked failure")

    result = await hass.config_entries.flow.async_init(
        keenetic.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_DATA
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def options_not_initialized(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test the error when the integration is not initialized."""
    entry = MockConfigEntry(domain=keenetic.DOMAIN, data=MOCK_DATA)
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_initialized")


@test
async def options_connection_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test updating options."""
    entry = MockConfigEntry(domain=keenetic.DOMAIN, data=MOCK_DATA)
    entry.add_to_hass(hass)

    def get_interfaces_error():
        raise ConnectionException("Mocked failure")

    entry.runtime_data = Mock(
        client=Mock(get_interfaces=Mock(wraps=get_interfaces_error))
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def options_interface_filter(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test the case when the default Home interface is missing on the router."""
    entry = MockConfigEntry(domain=keenetic.DOMAIN, data=MOCK_DATA)
    entry.add_to_hass(hass)

    entry.runtime_data = Mock(
        client=Mock(
            get_interfaces=Mock(
                return_value=[
                    InterfaceInfo.from_dict({"id": name, "type": "bridge"})
                    for name in ("not_a_home", "also_not_home")
                ]
            )
        )
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    interfaces_schema = next(
        i
        for i, s in result["data_schema"].schema.items()
        if i.schema == CONF_INTERFACES
    )
    expect(isinstance(interfaces_schema, vol.Required)).to_be(True)
    expect(interfaces_schema.default()).to_equal([])


@test
async def ssdp_works(
    hass: HomeAssistant = Depends(hass_fixture),
    _router_info_mock: MagicMock = Depends(router_info_mock),
) -> None:
    """Test host already configured and discovered."""
    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        keenetic.DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_SSDP},
        data=discovery_info,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.keenetic_ndms2.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        user_input = MOCK_DATA.copy()
        user_input.pop(CONF_HOST)
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=user_input
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(MOCK_NAME)
    expect(result2["data"]).to_equal(MOCK_DATA)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def ssdp_already_configured(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test host already configured and discovered."""
    entry = MockConfigEntry(
        domain=keenetic.DOMAIN, data=MOCK_DATA, options=MOCK_OPTIONS
    )
    entry.add_to_hass(hass)

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        keenetic.DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_SSDP},
        data=discovery_info,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def ssdp_ignored(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test unique ID ignored and discovered."""
    entry = MockConfigEntry(
        domain=keenetic.DOMAIN,
        source=config_entries.SOURCE_IGNORE,
        unique_id=MOCK_SSDP_DISCOVERY_INFO.upnp[ATTR_UPNP_UDN],
    )
    entry.add_to_hass(hass)

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        keenetic.DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_SSDP},
        data=discovery_info,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def ssdp_update_host(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test unique ID configured and discovered with the new host."""
    entry = MockConfigEntry(
        domain=keenetic.DOMAIN,
        data=MOCK_DATA,
        options=MOCK_OPTIONS,
        unique_id=MOCK_SSDP_DISCOVERY_INFO.upnp[ATTR_UPNP_UDN],
    )
    entry.add_to_hass(hass)

    new_ip = "10.10.10.10"
    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    discovery_info.ssdp_location = f"http://{new_ip}/"

    result = await hass.config_entries.flow.async_init(
        keenetic.DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_SSDP},
        data=discovery_info,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_HOST]).to_equal(new_ip)


@test
async def ssdp_reject_no_udn(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Discovered device has no UDN."""
    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    discovery_info.upnp = {**discovery_info.upnp}
    discovery_info.upnp.pop(ATTR_UPNP_UDN)

    result = await hass.config_entries.flow.async_init(
        keenetic.DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_SSDP},
        data=discovery_info,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_udn")


@test
async def ssdp_reject_non_keenetic(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Discovered device does not look like a keenetic router."""
    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    discovery_info.upnp = {**discovery_info.upnp}
    discovery_info.upnp[ATTR_UPNP_FRIENDLY_NAME] = "Suspicious device"
    result = await hass.config_entries.flow.async_init(
        keenetic.DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_SSDP},
        data=discovery_info,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_keenetic_ndms2")
