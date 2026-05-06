"""Test the Ituran config flow."""

from unittest.mock import AsyncMock

from pyituran.exceptions import IturanApiError, IturanAuthError
from tryke import Depends, expect, fixture, test

from homeassistant.components.ituran.const import (
    CONF_ID_OR_PASSPORT,
    CONF_MOBILE_ID,
    CONF_OTP,
    CONF_PHONE_NUMBER,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import setup_integration
from ._fixtures import mock_config_entry, mock_ituran, mock_setup_entry
from .const import MOCK_CONFIG_DATA

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor(
    _ituran: AsyncMock = Depends(mock_ituran),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


async def __do_successful_user_step(
    hass: HomeAssistant, result: ConfigFlowResult, ituran: AsyncMock
) -> ConfigFlowResult:
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_ID_OR_PASSPORT: MOCK_CONFIG_DATA[CONF_ID_OR_PASSPORT],
            CONF_PHONE_NUMBER: MOCK_CONFIG_DATA[CONF_PHONE_NUMBER],
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("otp")
    expect(result["errors"]).to_equal({})

    return result


async def __do_successful_otp_step(
    hass: HomeAssistant,
    result: ConfigFlowResult,
    ituran: AsyncMock,
) -> ConfigFlowResult:
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_OTP: "123456",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"Ituran {MOCK_CONFIG_DATA[CONF_ID_OR_PASSPORT]}")
    expect(result["data"][CONF_ID_OR_PASSPORT]).to_equal(
        MOCK_CONFIG_DATA[CONF_ID_OR_PASSPORT]
    )
    expect(result["data"][CONF_PHONE_NUMBER]).to_equal(
        MOCK_CONFIG_DATA[CONF_PHONE_NUMBER]
    )
    expect(result["data"][CONF_MOBILE_ID] is not None).to_be_truthy()
    expect(result["result"].unique_id).to_equal(MOCK_CONFIG_DATA[CONF_ID_OR_PASSPORT])
    expect(len(ituran.is_authenticated.mock_calls) > 0).to_be_truthy()
    expect(len(ituran.authenticate.mock_calls) > 0).to_be_truthy()

    return result


@test
async def full_user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ituran: AsyncMock = Depends(mock_ituran),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await __do_successful_user_step(hass, result, ituran)
    await __do_successful_otp_step(hass, result, ituran)


@test
async def invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ituran: AsyncMock = Depends(mock_ituran),
) -> None:
    """Test invalid credentials configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    ituran.request_otp.side_effect = IturanAuthError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_ID_OR_PASSPORT: MOCK_CONFIG_DATA[CONF_ID_OR_PASSPORT],
            CONF_PHONE_NUMBER: MOCK_CONFIG_DATA[CONF_PHONE_NUMBER],
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    ituran.request_otp.side_effect = None
    result = await __do_successful_user_step(hass, result, ituran)
    await __do_successful_otp_step(hass, result, ituran)


@test
async def invalid_otp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ituran: AsyncMock = Depends(mock_ituran),
) -> None:
    """Test invalid OTP configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await __do_successful_user_step(hass, result, ituran)

    ituran.authenticate.side_effect = IturanAuthError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_OTP: "123456",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_otp"})

    ituran.authenticate.side_effect = None
    await __do_successful_otp_step(hass, result, ituran)


@test.cases(
    test.case("cannot_connect", exception=IturanApiError, expected_error="cannot_connect"),
    test.case("unknown", exception=Exception, expected_error="unknown"),
)
async def errors(
    exception: type[Exception],
    expected_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    ituran: AsyncMock = Depends(mock_ituran),
    setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test connection errors during configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    ituran.request_otp.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_ID_OR_PASSPORT: MOCK_CONFIG_DATA[CONF_ID_OR_PASSPORT],
            CONF_PHONE_NUMBER: MOCK_CONFIG_DATA[CONF_PHONE_NUMBER],
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": expected_error})

    ituran.request_otp.side_effect = None
    result = await __do_successful_user_step(hass, result, ituran)

    ituran.authenticate.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_OTP: "123456",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    ituran.authenticate.side_effect = None
    await __do_successful_otp_step(hass, result, ituran)


@test
async def already_authenticated(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ituran: AsyncMock = Depends(mock_ituran),
) -> None:
    """Test user already authenticated configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    ituran.is_authenticated.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_ID_OR_PASSPORT: MOCK_CONFIG_DATA[CONF_ID_OR_PASSPORT],
            CONF_PHONE_NUMBER: MOCK_CONFIG_DATA[CONF_PHONE_NUMBER],
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"Ituran {MOCK_CONFIG_DATA[CONF_ID_OR_PASSPORT]}")
    expect(result["data"][CONF_ID_OR_PASSPORT]).to_equal(
        MOCK_CONFIG_DATA[CONF_ID_OR_PASSPORT]
    )
    expect(result["data"][CONF_PHONE_NUMBER]).to_equal(
        MOCK_CONFIG_DATA[CONF_PHONE_NUMBER]
    )
    expect(result["data"][CONF_MOBILE_ID]).to_equal(MOCK_CONFIG_DATA[CONF_MOBILE_ID])
    expect(result["result"].unique_id).to_equal(MOCK_CONFIG_DATA[CONF_ID_OR_PASSPORT])


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ituran: AsyncMock = Depends(mock_ituran),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauthenticating."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await __do_successful_user_step(hass, result, ituran)
    await __do_successful_otp_step(hass, result, ituran)

    await setup_integration(hass, entry)
    result = await entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_be_none()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("otp")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_OTP: "123456",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
