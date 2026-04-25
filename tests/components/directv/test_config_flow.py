"""Test the DirecTV config flow."""

import dataclasses
from unittest.mock import patch

from aiohttp import ClientError as HTTPClientError
from tryke import Depends, expect, fixture, test

from homeassistant.components.directv.const import CONF_RECEIVER_ID, DOMAIN
from homeassistant.config_entries import SOURCE_SSDP, SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import ATTR_UPNP_SERIAL

from . import (
    HOST,
    MOCK_SSDP_DISCOVERY_INFO,
    MOCK_USER_INPUT,
    RECEIVER_ID,
    UPNP_SERIAL,
    mock_connection,
    setup_integration,
)

from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fx,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def show_user_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the user set up form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
    )

    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)


@test
async def show_ssdp_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test that the ssdp confirmation form is served."""
    mock_connection(aioclient_mock)

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_SSDP}, data=discovery_info
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("ssdp_confirm")
    expect(result["description_placeholders"]).to_equal({CONF_NAME: HOST})


@test
async def cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test we show user form on connection error."""
    aioclient_mock.get("http://127.0.0.1:8080/info/getVersion", exc=HTTPClientError)

    user_input = MOCK_USER_INPUT.copy()
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=user_input,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def ssdp_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test we abort SSDP flow on connection error."""
    aioclient_mock.get("http://127.0.0.1:8080/info/getVersion", exc=HTTPClientError)

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=discovery_info,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def ssdp_confirm_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test we abort SSDP flow on connection error."""
    aioclient_mock.get("http://127.0.0.1:8080/info/getVersion", exc=HTTPClientError)

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP, CONF_HOST: HOST, CONF_NAME: HOST},
        data=discovery_info,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def user_device_exists_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test we abort user flow if DirecTV receiver already configured."""
    await setup_integration(hass, aioclient_mock, skip_entry_setup=True)

    user_input = MOCK_USER_INPUT.copy()
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=user_input,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def ssdp_device_exists_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test we abort SSDP flow if DirecTV receiver already configured."""
    await setup_integration(hass, aioclient_mock, skip_entry_setup=True)

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=discovery_info,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def ssdp_with_receiver_id_device_exists_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test we abort SSDP flow if DirecTV receiver already configured."""
    await setup_integration(hass, aioclient_mock, skip_entry_setup=True)

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    discovery_info.upnp[ATTR_UPNP_SERIAL] = UPNP_SERIAL
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=discovery_info,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test we show user form on unknown error."""
    user_input = MOCK_USER_INPUT.copy()
    with patch(
        "homeassistant.components.directv.config_flow.DIRECTV.update",
        side_effect=Exception,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={CONF_SOURCE: SOURCE_USER},
            data=user_input,
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def ssdp_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test we abort SSDP flow on unknown error."""
    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    with patch(
        "homeassistant.components.directv.config_flow.DIRECTV.update",
        side_effect=Exception,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={CONF_SOURCE: SOURCE_SSDP},
            data=discovery_info,
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def ssdp_confirm_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test we abort SSDP flow on unknown error."""
    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    with patch(
        "homeassistant.components.directv.config_flow.DIRECTV.update",
        side_effect=Exception,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={CONF_SOURCE: SOURCE_SSDP, CONF_HOST: HOST, CONF_NAME: HOST},
            data=discovery_info,
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def full_user_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test the full manual user flow from start to finish."""
    mock_connection(aioclient_mock)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    user_input = MOCK_USER_INPUT.copy()
    with patch("homeassistant.components.directv.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(HOST)

    expect(bool(result["data"])).to_be(True)
    expect(result["data"][CONF_HOST]).to_equal(HOST)
    expect(result["data"][CONF_RECEIVER_ID]).to_equal(RECEIVER_ID)


@test
async def full_ssdp_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test the full SSDP flow from start to finish."""
    mock_connection(aioclient_mock)

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_SSDP}, data=discovery_info
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("ssdp_confirm")
    expect(result["description_placeholders"]).to_equal({CONF_NAME: HOST})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(HOST)

    expect(bool(result["data"])).to_be(True)
    expect(result["data"][CONF_HOST]).to_equal(HOST)
    expect(result["data"][CONF_RECEIVER_ID]).to_equal(RECEIVER_ID)
