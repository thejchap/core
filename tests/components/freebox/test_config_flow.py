"""Tests for the Freebox config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, Mock, patch

from freebox_api.exceptions import (
    AuthorizationError,
    HttpRequestError,
    InvalidTokenError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.freebox.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.components.freebox._fixtures import (
    mock_path,
    mock_router_bridge_mode_error,
    router,
    router_bridge_mode,
)
from tests.components.freebox.const import MOCK_HOST, MOCK_PORT
from tests.hass_fixtures import hass as hass_fixture

MOCK_ZEROCONF_DATA = ZeroconfServiceInfo(
    ip_address=ip_address("192.168.0.254"),
    ip_addresses=[ip_address("192.168.0.254")],
    port=80,
    hostname="Freebox-Server.local.",
    type="_fbx-api._tcp.local.",
    name="Freebox Server._fbx-api._tcp.local.",
    properties={
        "api_version": "8.0",
        "device_type": "FreeboxServer1,2",
        "api_base_url": "/api/",
        "uid": "b15ab20debb399f95001a9ca207d2777",
        "https_available": "1",
        "https_port": f"{MOCK_PORT}",
        "box_model": "fbxgw-r2/full",
        "box_model_name": "Freebox Server (r2)",
        "api_domain": MOCK_HOST,
    },
)


@fixture
def _trigger_executor(_m: None = Depends(mock_path)) -> None:
    """Trigger the hook executor path."""
    return None


async def _internal_test_link(hass: HomeAssistant) -> None:
    """Test linking internal, common to both router modes."""
    with patch(
        "homeassistant.components.freebox.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT},
        )

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["result"].unique_id).to_equal(MOCK_HOST)
        expect(result["title"]).to_equal(MOCK_HOST)
        expect(result["data"][CONF_HOST]).to_equal(MOCK_HOST)
        expect(result["data"][CONF_PORT]).to_equal(MOCK_PORT)
        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user config."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("link")


@test
async def zeroconf(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test zeroconf step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=MOCK_ZEROCONF_DATA,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("link")


@test
async def link(
    hass: HomeAssistant = Depends(hass_fixture),
    _router: Mock = Depends(router),
) -> None:
    """Test link with standard router mode."""
    await _internal_test_link(hass)


@test
async def link_bridge_mode(
    hass: HomeAssistant = Depends(hass_fixture),
    _router_bridge_mode: Mock = Depends(router_bridge_mode),
) -> None:
    """Test linking for a freebox in bridge mode."""
    await _internal_test_link(hass)


@test
async def link_bridge_mode_error(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_router_bridge_mode_error: Mock = Depends(mock_router_bridge_mode_error),
) -> None:
    """Test linking for a freebox in bridge mode, unknown error received from API."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT},
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def abort_if_already_setup(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we abort if component is already setup."""
    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT},
        unique_id=MOCK_HOST,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def on_link_failed(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test when we have errors during linking the router."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT},
    )

    with patch(
        "homeassistant.components.freebox.router.Freepybox.open",
        side_effect=AuthorizationError(),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "register_failed"})

    with patch(
        "homeassistant.components.freebox.router.Freepybox.open",
        side_effect=HttpRequestError(),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with patch(
        "homeassistant.components.freebox.router.Freepybox.open",
        side_effect=InvalidTokenError(),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "unknown"})


@test
async def zeroconf_missing_api_domain(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test zeroconf flow aborts if api_domain is missing from properties."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.254"),
            ip_addresses=[ip_address("192.168.1.254")],
            port=80,
            hostname="Freebox-Server.local.",
            type="_fbx-api._tcp.local.",
            name="Freebox Server._fbx-api._tcp.local.",
            properties={"api_version": "8.0"},
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("missing_api_domain")
