"""Test the Ituran config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

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

from .const import MOCK_CONFIG_DATA

from tests.components.ituran._fixtures import mock_ituran, mock_setup_entry
from tests.hass_fixtures import hass as hass_fixture, mock_network


async def _do_successful_user_step(
    hass: HomeAssistant, result: ConfigFlowResult, mock_ituran: AsyncMock
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


async def _do_successful_otp_step(
    hass: HomeAssistant,
    result: ConfigFlowResult,
    mock_ituran: AsyncMock,
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
    expect(result["data"][CONF_MOBILE_ID] is not None).to_be(True)
    expect(result["result"].unique_id).to_equal(MOCK_CONFIG_DATA[CONF_ID_OR_PASSPORT])
    expect(len(mock_ituran.is_authenticated.mock_calls) > 0).to_be(True)
    expect(len(mock_ituran.authenticate.mock_calls) > 0).to_be(True)

    return result


@fixture
def _mock_zeroconf() -> MagicMock:
    """Patch zeroconf so tests don't require a real zeroconf instance."""
    from zeroconf import DNSCache

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch("homeassistant.components.zeroconf.discovery.AsyncServiceBrowser"),
    ):
        zc = mock_zc.return_value
        zc.async_add_service_listener = AsyncMock()
        zc.async_remove_service_listener = AsyncMock()
        zc.async_register_service = AsyncMock()
        zc.async_update_service = AsyncMock()
        zc.cache = DNSCache()
        yield mock_zc


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mz: MagicMock = Depends(_mock_zeroconf),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def full_user_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_ituran: AsyncMock = Depends(mock_ituran),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await _do_successful_user_step(hass, result, mock_ituran)
    await _do_successful_otp_step(hass, result, mock_ituran)


@test
async def invalid_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_ituran: AsyncMock = Depends(mock_ituran),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test invalid credentials configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    mock_ituran.request_otp.side_effect = IturanAuthError
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

    mock_ituran.request_otp.side_effect = None
    result = await _do_successful_user_step(hass, result, mock_ituran)
    await _do_successful_otp_step(hass, result, mock_ituran)


@test
async def invalid_otp(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_ituran: AsyncMock = Depends(mock_ituran),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test invalid OTP configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await _do_successful_user_step(hass, result, mock_ituran)

    mock_ituran.authenticate.side_effect = IturanAuthError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_OTP: "123456",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_otp"})

    mock_ituran.authenticate.side_effect = None
    await _do_successful_otp_step(hass, result, mock_ituran)


@test.cases(
    test.case("cannot_connect", exception=IturanApiError, expected_error="cannot_connect"),
    test.case("unknown", exception=Exception, expected_error="unknown"),
)
async def errors(
    exception: type[Exception],
    expected_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_ituran: AsyncMock = Depends(mock_ituran),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test connection errors during configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    mock_ituran.request_otp.side_effect = exception
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

    mock_ituran.request_otp.side_effect = None
    result = await _do_successful_user_step(hass, result, mock_ituran)

    mock_ituran.authenticate.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_OTP: "123456",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    mock_ituran.authenticate.side_effect = None
    await _do_successful_otp_step(hass, result, mock_ituran)


@test
async def already_authenticated(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_ituran: AsyncMock = Depends(mock_ituran),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user already authenticated configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    mock_ituran.is_authenticated.return_value = True
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
