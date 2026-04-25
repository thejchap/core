"""Tests for the Modern Forms config flow."""

from ipaddress import ip_address
from unittest.mock import MagicMock, patch

import aiohttp
from aiomodernforms import ModernFormsConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.modern_forms.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME, CONTENT_TYPE_JSON
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from . import init_integration

from tests.common import async_load_fixture
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_user_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test the full manual user flow from start to finish."""
    aioclient_mock.post(
        "http://192.168.1.123:80/mf",
        text=await async_load_fixture(hass, "device_info.json", DOMAIN),
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result.get("step_id")).to_equal("user")
    expect(result.get("type")).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.modern_forms.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_HOST: "192.168.1.123"}
        )

    expect(result2.get("title")).to_equal("ModernFormsFan")
    expect("data" in result2).to_be(True)
    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["data"][CONF_HOST]).to_equal("192.168.1.123")
    expect(result2["data"][CONF_MAC]).to_equal("AA:BB:CC:DD:EE:FF")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def full_zeroconf_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test the full manual user flow from start to finish."""
    aioclient_mock.post(
        "http://192.168.1.123:80/mf",
        text=await async_load_fixture(hass, "device_info.json", DOMAIN),
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=None,
            properties={},
            type="mock_type",
        ),
    )

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)

    expect(result.get("description_placeholders")).to_equal({CONF_NAME: "example"})
    expect(result.get("step_id")).to_equal("zeroconf_confirm")
    expect(result.get("type")).to_be(FlowResultType.FORM)

    flow = hass.config_entries.flow._progress[flows[0]["flow_id"]]
    expect(flow.host).to_equal("192.168.1.123")
    expect(flow.name).to_equal("example")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result2.get("title")).to_equal("example")
    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)

    expect("data" in result2).to_be(True)
    expect(result2["data"][CONF_HOST]).to_equal("192.168.1.123")
    expect(result2["data"][CONF_MAC]).to_equal("AA:BB:CC:DD:EE:FF")


@test
async def connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test we show user form on Modern Forms connection error."""
    with patch(
        "homeassistant.components.modern_forms.coordinator.ModernFormsDevice.update",
        side_effect=ModernFormsConnectionError,
    ):
        aioclient_mock.post("http://example.com/mf", exc=aiohttp.ClientError)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "example.com"},
        )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("errors")).to_equal({"base": "cannot_connect"})


@test
async def zeroconf_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test we abort zeroconf flow on Modern Forms connection error."""
    with patch(
        "homeassistant.components.modern_forms.coordinator.ModernFormsDevice.update",
        side_effect=ModernFormsConnectionError,
    ):
        aioclient_mock.post("http://192.168.1.123/mf", exc=aiohttp.ClientError)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_ZEROCONF},
            data=ZeroconfServiceInfo(
                ip_address=ip_address("192.168.1.123"),
                ip_addresses=[ip_address("192.168.1.123")],
                hostname="example.local.",
                name="mock_name",
                port=None,
                properties={},
                type="mock_type",
            ),
        )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("cannot_connect")


@test
async def zeroconf_confirm_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test we abort zeroconf flow on Modern Forms connection error."""
    with patch(
        "homeassistant.components.modern_forms.coordinator.ModernFormsDevice.update",
        side_effect=ModernFormsConnectionError,
    ):
        aioclient_mock.post("http://192.168.1.123:80/mf", exc=aiohttp.ClientError)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": SOURCE_ZEROCONF,
                CONF_HOST: "example.com",
                CONF_NAME: "test",
            },
            data=ZeroconfServiceInfo(
                ip_address=ip_address("192.168.1.123"),
                ip_addresses=[ip_address("192.168.1.123")],
                hostname="example.com.",
                name="mock_name",
                port=None,
                properties={},
                type="mock_type",
            ),
        )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("cannot_connect")


@test
async def user_device_exists_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test we abort zeroconf flow if Modern Forms device already configured."""
    aioclient_mock.post(
        "http://192.168.1.123:80/mf",
        text=await async_load_fixture(hass, "device_info.json", DOMAIN),
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    await init_integration(hass, aioclient_mock, skip_setup=True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.123"},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test
async def zeroconf_with_mac_device_exists_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test we abort zeroconf flow if a Modern Forms device already configured."""
    await init_integration(hass, aioclient_mock, skip_setup=True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=None,
            properties={CONF_MAC: "AA:BB:CC:DD:EE:FF"},
            type="mock_type",
        ),
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")
