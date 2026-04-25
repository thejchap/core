"""Tests for the Atag config flow."""

from unittest.mock import AsyncMock, PropertyMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.atag import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import UID, USER_INPUT, init_integration, mock_connection
from ._fixtures import mock_pyatag_sleep, mock_setup_entry

from tests.hass_fixtures import aioclient_mock, hass as hass_fixture, mock_network
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _sleep: None = Depends(mock_pyatag_sleep),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def show_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test that the form is served with no input."""
    mock_connection(aioclient)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def adding_second_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test that only one Atag configuration is allowed."""
    await init_integration(hass, aioclient, unique_id=UID)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    with patch(
        "pyatag.AtagOne.id",
        new_callable=PropertyMock(return_value="secondary_device"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=USER_INPUT
        )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test we show user form on Atag connection error."""
    mock_connection(aioclient, conn_error=True)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def unauthorized(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test we show correct form when Unauthorized error is raised."""
    mock_connection(aioclient, authorized=False)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=USER_INPUT,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "unauthorized"})


@test
async def full_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test registering an integration and finishing flow works."""
    mock_connection(aioclient)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=USER_INPUT,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(UID)
    expect(result["result"].unique_id).to_equal(UID)
