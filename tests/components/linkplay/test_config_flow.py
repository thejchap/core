"""Tests for the LinkPlay config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock

from linkplay.exceptions import LinkPlayRequestException
from linkplay.manufacturers import MANUFACTURER_WIIM
from tryke import Depends, expect, fixture, test

from homeassistant.components.linkplay.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    HOST,
    HOST_REENTRY,
    NAME,
    UUID,
    mock_linkplay_factory_bridge,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

ZEROCONF_DISCOVERY = ZeroconfServiceInfo(
    ip_address=ip_address(HOST),
    ip_addresses=[ip_address(HOST)],
    hostname=f"{NAME}.local.",
    name=f"{NAME}._linkplay._tcp.local.",
    port=59152,
    type="_linkplay._tcp.local.",
    properties={
        "uuid": f"uuid:{UUID}",
        "mac": "00:2F:69:01:84:3A",
        "security": "https 2.0",
        "upnp": "1.0.0",
        "bootid": "1f347886-1dd2-11b2-86ab-aa0cd2803583",
    },
)

ZEROCONF_DISCOVERY_RE_ENTRY = ZeroconfServiceInfo(
    ip_address=ip_address(HOST_REENTRY),
    ip_addresses=[ip_address(HOST_REENTRY)],
    hostname=f"{NAME}.local.",
    name=f"{NAME}._linkplay._tcp.local.",
    port=59152,
    type="_linkplay._tcp.local.",
    properties={
        "uuid": f"uuid:{UUID}",
        "mac": "00:2F:69:01:84:3A",
        "security": "https 2.0",
        "upnp": "1.0.0",
        "bootid": "1f347886-1dd2-11b2-86ab-aa0cd2803583",
    },
)


@fixture
def _trigger_executor(_mn: None = Depends(mock_network)) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def user_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_linkplay_factory_bridge: AsyncMock = Depends(mock_linkplay_factory_bridge),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user setup config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: HOST},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(NAME)
    expect(result["data"]).to_equal({CONF_HOST: HOST})
    expect(result["result"].unique_id).to_equal(UUID)


@test
async def user_flow_re_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_linkplay_factory_bridge: AsyncMock = Depends(mock_linkplay_factory_bridge),
) -> None:
    """Test user setup config flow when an entry with the same unique id already exists."""
    entry = MockConfigEntry(
        data={CONF_HOST: HOST},
        domain=DOMAIN,
        title=NAME,
        unique_id=UUID,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: HOST_REENTRY},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_linkplay_factory_bridge: AsyncMock = Depends(mock_linkplay_factory_bridge),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test Zeroconf flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(NAME)
    expect(result["data"]).to_equal({CONF_HOST: HOST})
    expect(result["result"].unique_id).to_equal(UUID)


@test
async def zeroconf_flow_re_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_linkplay_factory_bridge: AsyncMock = Depends(mock_linkplay_factory_bridge),
) -> None:
    """Test Zeroconf flow when an entry with the same unique id already exists."""
    entry = MockConfigEntry(
        data={CONF_HOST: HOST},
        domain=DOMAIN,
        title=NAME,
        unique_id=UUID,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY_RE_ENTRY,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_flow_errors(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_linkplay_factory_bridge: AsyncMock = Depends(mock_linkplay_factory_bridge),
) -> None:
    """Test flow when the device discovered through Zeroconf cannot be reached."""
    mock_linkplay_factory_bridge.side_effect = (LinkPlayRequestException("Error"),)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def zeroconf_flow_ignores_wiim_device(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_linkplay_factory_bridge: AsyncMock = Depends(mock_linkplay_factory_bridge),
) -> None:
    """Test Zeroconf discovery is ignored for WiiM devices."""
    mock_linkplay_factory_bridge.return_value.device.manufacturer = MANUFACTURER_WIIM

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_linkplay_device")


@test
async def user_flow_errors(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_linkplay_factory_bridge: AsyncMock = Depends(mock_linkplay_factory_bridge),
) -> None:
    """Test flow when the device cannot be reached."""
    mock_linkplay_factory_bridge.side_effect = (LinkPlayRequestException("Error"),)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: HOST},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    mock_linkplay_factory_bridge.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: HOST},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(NAME)
    expect(result["data"]).to_equal({CONF_HOST: HOST})
    expect(result["result"].unique_id).to_equal(UUID)


@test
async def zeroconf_no_probe_existing_device(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_linkplay_factory_bridge: AsyncMock = Depends(mock_linkplay_factory_bridge),
) -> None:
    """Test we do not probe the device is the host is already configured."""
    entry = MockConfigEntry(
        data={CONF_HOST: HOST},
        domain=DOMAIN,
        title=NAME,
        unique_id=UUID,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(len(mock_linkplay_factory_bridge.mock_calls)).to_equal(0)
