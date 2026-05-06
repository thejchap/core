"""Tests for the Agent DVR config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.agent_dvr.const import DOMAIN, SERVER_URL
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT, CONTENT_TYPE_JSON
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import init_integration
from ._fixtures import mock_setup_entry

from tests.common import async_load_fixture
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def show_user_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the user set up form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)


@test
async def user_device_exists_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test we abort flow if Agent device already configured."""
    await init_integration(hass, aioclient_mock)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "example.local", CONF_PORT: 8090},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)


@test
async def connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test we show user form on Agent connection error."""

    aioclient_mock.get("http://example.local:8090/command.cgi?cmd=getStatus", text="")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "example.local", CONF_PORT: 8090},
    )

    expect(result["errors"]["base"]).to_equal("cannot_connect")
    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)


@test
async def full_user_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test the full manual user flow from start to finish."""
    aioclient_mock.get(
        "http://example.local:8090/command.cgi?cmd=getStatus",
        text=await async_load_fixture(hass, "status.json", DOMAIN),
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    aioclient_mock.get(
        "http://example.local:8090/command.cgi?cmd=getObjects",
        text=await async_load_fixture(hass, "objects.json", DOMAIN),
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "example.local", CONF_PORT: 8090}
    )

    expect(result["data"][CONF_HOST]).to_equal("example.local")
    expect(result["data"][CONF_PORT]).to_equal(8090)
    expect(result["data"][SERVER_URL]).to_equal("http://example.local:8090/")
    expect(result["title"]).to_equal("DESKTOP")
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    entries = hass.config_entries.async_entries(DOMAIN)
    expect(entries[0].unique_id).to_equal("c0715bba-c2d0-48ef-9e3e-bc81c9ea4447")
