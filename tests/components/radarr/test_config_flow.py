"""Test Radarr config flow."""

from __future__ import annotations

from unittest.mock import patch

from aiopyarr import exceptions
from freezegun import freeze_time
from tryke import Depends, expect, fixture, test

from homeassistant.components.radarr.const import DEFAULT_NAME, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_SOURCE, CONF_URL, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    API_KEY,
    CONF_DATA,
    MOCK_REAUTH_INPUT,
    MOCK_USER_INPUT,
    URL,
    mock_connection,
    mock_connection_error,
    mock_connection_invalid_auth,
    patch_async_setup_entry,
    setup_integration,
)

from tests.hass_fixtures import aioclient_mock, hass as hass_fixture, mock_network
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def show_user_form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that the user set up form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
    )

    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)


@test
async def cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    aio_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test we show user form on connection error."""
    mock_connection_error(aio_mock)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=MOCK_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def invalid_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    aio_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test we show user form on invalid auth."""
    mock_connection_invalid_auth(aio_mock)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data=MOCK_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})


@test
async def wrong_app(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we show user form on wrong app."""
    with patch(
        "homeassistant.components.radarr.config_flow.RadarrClient.async_try_zeroconf",
        side_effect=exceptions.ArrWrongAppException,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={CONF_SOURCE: SOURCE_USER},
            data={CONF_URL: URL, CONF_VERIFY_SSL: False},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]["base"]).to_equal("wrong_app")


@test
async def zero_conf_failure(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we show user form on api key retrieval failure."""
    with patch(
        "homeassistant.components.radarr.config_flow.RadarrClient.async_try_zeroconf",
        side_effect=exceptions.ArrZeroConfException,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={CONF_SOURCE: SOURCE_USER},
            data={CONF_URL: URL, CONF_VERIFY_SSL: False},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]["base"]).to_equal("zeroconf_failed")


@test
async def unknown_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we show user form on unknown error."""
    with patch(
        "homeassistant.components.radarr.config_flow.RadarrClient.async_get_system_status",
        side_effect=exceptions.ArrException,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={CONF_SOURCE: SOURCE_USER},
            data=MOCK_USER_INPUT,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "unknown"})


@test
async def zero_conf(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test the manual flow for zero config."""
    with (
        patch(
            "homeassistant.components.radarr.config_flow.RadarrClient.async_try_zeroconf",
            return_value=("v3", API_KEY, "/test"),
        ),
        patch_async_setup_entry(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={CONF_SOURCE: SOURCE_USER},
            data={CONF_URL: URL, CONF_VERIFY_SSL: False},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal(CONF_DATA)


@test
async def url_rewrite(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test auth flow url rewrite."""
    with (
        patch(
            "homeassistant.components.radarr.config_flow.RadarrClient.async_try_zeroconf",
            return_value=("v3", API_KEY, "/test"),
        ),
        patch_async_setup_entry(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={CONF_SOURCE: SOURCE_USER},
            data={CONF_URL: "https://192.168.1.100/test", CONF_VERIFY_SSL: False},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"][CONF_URL]).to_equal("https://192.168.1.100:443/test")


@test
async def full_reauth_flow_implementation(
    hass: HomeAssistant = Depends(hass_fixture),
    aio_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test the manual reauth flow from start to finish."""
    with freeze_time("2021-12-03 00:00:00+00:00"):
        entry = await setup_integration(hass, aio_mock)
        result = await entry.start_reauth_flow(hass)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("reauth_confirm")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")

        with patch_async_setup_entry() as mock_setup_entry:
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], user_input=MOCK_REAUTH_INPUT
            )
            await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("reauth_successful")

        expect(entry.data).to_equal(CONF_DATA | {CONF_API_KEY: "test-api-key-reauth"})

        mock_setup_entry.assert_called_once()


@test
async def full_user_flow_implementation(
    hass: HomeAssistant = Depends(hass_fixture),
    aio_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test the full manual user flow from start to finish."""
    mock_connection(aio_mock)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch_async_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=MOCK_USER_INPUT,
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal(CONF_DATA)
    expect(result["data"][CONF_URL]).to_equal("http://192.168.1.189:7887/test")
