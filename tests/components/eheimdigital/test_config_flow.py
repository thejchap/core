"""Tests the config flow of EHEIM Digital."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import ClientConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.eheimdigital.const import DOMAIN
from homeassistant.config_entries import (
    SOURCE_USER,
    SOURCE_ZEROCONF,
)
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    classic_led_ctrl_mock,
    classic_vario_mock,
    eheimdigital_hub_mock,
    filter_mock,
    heater_mock,
    mock_config_entry,
    reeflex_mock,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network

ZEROCONF_DISCOVERY = ZeroconfServiceInfo(
    ip_address=ip_address("192.0.2.1"),
    ip_addresses=[ip_address("192.0.2.1")],
    hostname="eheimdigital.local.",
    name="eheimdigital._http._tcp.local.",
    port=80,
    type="_http._tcp.local.",
    properties={},
)

USER_INPUT = {CONF_HOST: "eheimdigital"}


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
) -> HomeAssistant:
    """Anchor fixture so tryke fully resolves hass."""
    return hass


@test
@patch("homeassistant.components.eheimdigital.config_flow.asyncio.Event", new=AsyncMock)
async def full_flow(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hub_mock: AsyncMock = Depends(eheimdigital_hub_mock),
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(USER_INPUT[CONF_HOST])
    expect(result["data"]).to_equal(USER_INPUT)
    expect(result["result"].unique_id).to_equal(hub_mock.return_value.main.mac_address)


@test.cases(
    test.case(
        "connection_error",
        side_effect=ClientConnectionError(),
        error_value="cannot_connect",
    ),
    test.case(
        "unknown",
        side_effect=Exception(),
        error_value="unknown",
    ),
)
@patch("homeassistant.components.eheimdigital.config_flow.asyncio.Event", new=AsyncMock)
async def flow_errors(
    *,
    side_effect: BaseException,
    error_value: str,
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hub_mock: AsyncMock = Depends(eheimdigital_hub_mock),
) -> None:
    """Test flow errors."""
    hub_mock.return_value.connect.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_value})

    hub_mock.return_value.connect.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(USER_INPUT[CONF_HOST])
    expect(result["data"]).to_equal(USER_INPUT)
    expect(result["result"].unique_id).to_equal(hub_mock.return_value.main.mac_address)


@test
@patch("homeassistant.components.eheimdigital.config_flow.asyncio.Event", new=AsyncMock)
async def zeroconf_flow(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hub_mock: AsyncMock = Depends(eheimdigital_hub_mock),
) -> None:
    """Test zeroconf flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(ZEROCONF_DISCOVERY.host)
    expect(result["data"]).to_equal({CONF_HOST: ZEROCONF_DISCOVERY.host})
    expect(result["result"].unique_id).to_equal(hub_mock.return_value.main.mac_address)


@test.cases(
    test.case(
        "connection_error",
        side_effect=ClientConnectionError(),
        error_value="cannot_connect",
    ),
    test.case(
        "unknown",
        side_effect=Exception(),
        error_value="unknown",
    ),
)
@patch("homeassistant.components.eheimdigital.config_flow.asyncio.Event", new=AsyncMock)
async def zeroconf_flow_errors(
    *,
    side_effect: BaseException,
    error_value: str,
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hub_mock: MagicMock = Depends(eheimdigital_hub_mock),
) -> None:
    """Test zeroconf flow errors."""
    hub_mock.return_value.connect.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(error_value)


@test
@patch("homeassistant.components.eheimdigital.config_flow.asyncio.Event", new=AsyncMock)
async def abort(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hub_mock: AsyncMock = Depends(eheimdigital_hub_mock),
) -> None:
    """Test flow abort on matching data or unique_id."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    result2 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    expect(result2["type"]).to_be(FlowResultType.FORM)

    result2 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")

    result3 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    expect(result3["type"]).to_be(FlowResultType.FORM)

    result2 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        {CONF_HOST: "eheimdigital2"},
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test.skip("reconfigure flow needs init_integration with full setup")
async def reconfigure(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test reconfigure flow."""


@test.skip("reconfigure flow needs init_integration with full setup")
async def reconfigure_different_device(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test reconfigure flow with different device."""
