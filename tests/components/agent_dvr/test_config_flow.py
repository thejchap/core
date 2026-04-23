"""Tests for the Agent DVR config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.agent_dvr.const import DOMAIN, SERVER_URL
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT, CONTENT_TYPE_JSON
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import async_load_fixture
from tests.components.agent_dvr._fixtures import mock_setup_entry
from tests.hass_fixtures import aioclient_mock, hass, mock_network
from tests.test_util.aiohttp import AiohttpClientMocker

from . import init_integration


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def show_user_form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the user set up form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["step_id"]).to_equal("user")
    expect(result["type"] is FlowResultType.FORM).to_be(True)


@test
async def user_device_exists_abort(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we abort flow if Agent device already configured."""
    await init_integration(hass, aioclient_mock)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "example.local", CONF_PORT: 8090},
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)


@test
async def connection_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
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
    expect(result["type"] is FlowResultType.FORM).to_be(True)


@test
async def full_user_flow_implementation(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
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
    expect(result["type"] is FlowResultType.FORM).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "example.local", CONF_PORT: 8090}
    )

    expect(result["data"][CONF_HOST]).to_equal("example.local")
    expect(result["data"][CONF_PORT]).to_equal(8090)
    expect(result["data"][SERVER_URL]).to_equal("http://example.local:8090/")
    expect(result["title"]).to_equal("DESKTOP")
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)

    entries = hass.config_entries.async_entries(DOMAIN)
    expect(entries[0].unique_id).to_equal("c0715bba-c2d0-48ef-9e3e-bc81c9ea4447")
