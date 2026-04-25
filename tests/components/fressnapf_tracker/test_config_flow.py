"""Test the Fressnapf Tracker config flow."""

from unittest.mock import AsyncMock, MagicMock

from fressnapftracker import (
    FressnapfTrackerInvalidPhoneNumberError,
    FressnapfTrackerInvalidTokenError,
    SmsCodeResponse,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.fressnapf_tracker.const import (
    CONF_PHONE_NUMBER,
    CONF_SMS_CODE,
    CONF_USER_ID,
    DOMAIN,
)
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    MOCK_ACCESS_TOKEN,
    MOCK_PHONE_NUMBER,
    MOCK_USER_ID,
    mock_api_client_coordinator,
    mock_api_client_init,
    mock_auth_client,
    mock_config_entry,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _auth_client: MagicMock = Depends(mock_auth_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PHONE_NUMBER: MOCK_PHONE_NUMBER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("sms_code")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_SMS_CODE: "0123456"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MOCK_PHONE_NUMBER)
    expect(result["data"]).to_equal(
        {
            CONF_PHONE_NUMBER: MOCK_PHONE_NUMBER,
            CONF_USER_ID: MOCK_USER_ID,
            CONF_ACCESS_TOKEN: MOCK_ACCESS_TOKEN,
        }
    )
    expect(result["context"]["unique_id"]).to_equal(str(MOCK_USER_ID))
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "invalid_phone_number",
        side_effect=FressnapfTrackerInvalidPhoneNumberError,
        error="invalid_phone_number",
    ),
    test.case("unknown", side_effect=Exception, error="unknown"),
)
async def user_flow_request_sms_code_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    auth_client: MagicMock = Depends(mock_auth_client),
    *,
    side_effect: Exception,
    error: str,
) -> None:
    """Test user flow with errors."""
    auth_client.request_sms_code.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PHONE_NUMBER: "invalid"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": error})

    auth_client.request_sms_code.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PHONE_NUMBER: MOCK_PHONE_NUMBER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("sms_code")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_SMS_CODE: "0123456"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case(
        "invalid_sms_code",
        side_effect=FressnapfTrackerInvalidTokenError,
        error="invalid_sms_code",
    ),
    test.case("unknown", side_effect=Exception, error="unknown"),
)
async def user_flow_verify_phone_number_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    auth_client: MagicMock = Depends(mock_auth_client),
    *,
    side_effect: Exception,
    error: str,
) -> None:
    """Test user flow with invalid SMS code."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PHONE_NUMBER: MOCK_PHONE_NUMBER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("sms_code")

    auth_client.verify_phone_number.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_SMS_CODE: "999999"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("sms_code")
    expect(result["errors"]).to_equal({"base": error})

    auth_client.verify_phone_number.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_SMS_CODE: "0123456"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_flow_duplicate_user_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _auth_client: MagicMock = Depends(mock_auth_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test user flow aborts on duplicate user_id."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PHONE_NUMBER: f"{MOCK_PHONE_NUMBER}123"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_flow_duplicate_phone_number(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _auth_client: MagicMock = Depends(mock_auth_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test user flow aborts on duplicate phone number."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PHONE_NUMBER: MOCK_PHONE_NUMBER},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


# Reauth + reconfigure flows: each was a parametrize with 2 lambda starters.
# In tryke, expand by hand into concrete tests.


async def _reauth_reconfigure_success(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    flow_starter,
    expected_step_id: str,
    expected_sms_step_id: str,
    expected_reason: str,
) -> None:
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await flow_starter(config_entry, hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(expected_step_id)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PHONE_NUMBER: MOCK_PHONE_NUMBER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(expected_sms_step_id)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_SMS_CODE: "0123456"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(expected_reason)


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api_init: MagicMock = Depends(mock_api_client_init),
    _api_coord: MagicMock = Depends(mock_api_client_coordinator),
    _auth: MagicMock = Depends(mock_auth_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the reauth flow."""
    await _reauth_reconfigure_success(
        hass,
        config_entry,
        lambda entry, h: entry.start_reauth_flow(h),
        "reauth_confirm",
        "reauth_sms_code",
        "reauth_successful",
    )


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api_init: MagicMock = Depends(mock_api_client_init),
    _api_coord: MagicMock = Depends(mock_api_client_coordinator),
    _auth: MagicMock = Depends(mock_auth_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the reconfigure flow."""
    await _reauth_reconfigure_success(
        hass,
        config_entry,
        lambda entry, h: entry.start_reconfigure_flow(h),
        "reconfigure",
        "reconfigure_sms_code",
        "reconfigure_successful",
    )


async def _reauth_reconfigure_invalid_phone(
    hass: HomeAssistant,
    auth_client: MagicMock,
    config_entry: MockConfigEntry,
    flow_starter,
    expected_step_id: str,
    expected_sms_step_id: str,
    expected_reason: str,
) -> None:
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await flow_starter(config_entry, hass)

    auth_client.request_sms_code.side_effect = FressnapfTrackerInvalidPhoneNumberError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PHONE_NUMBER: "invalid"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(expected_step_id)
    expect(result["errors"]).to_equal({"base": "invalid_phone_number"})

    auth_client.request_sms_code.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PHONE_NUMBER: MOCK_PHONE_NUMBER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(expected_sms_step_id)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_SMS_CODE: "0123456"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(expected_reason)


@test
async def reauth_flow_invalid_phone_number(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api_init: MagicMock = Depends(mock_api_client_init),
    _api_coord: MagicMock = Depends(mock_api_client_coordinator),
    auth_client: MagicMock = Depends(mock_auth_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow with invalid phone number."""
    await _reauth_reconfigure_invalid_phone(
        hass,
        auth_client,
        config_entry,
        lambda entry, h: entry.start_reauth_flow(h),
        "reauth_confirm",
        "reauth_sms_code",
        "reauth_successful",
    )


@test
async def reconfigure_flow_invalid_phone_number(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api_init: MagicMock = Depends(mock_api_client_init),
    _api_coord: MagicMock = Depends(mock_api_client_coordinator),
    auth_client: MagicMock = Depends(mock_auth_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow with invalid phone number."""
    await _reauth_reconfigure_invalid_phone(
        hass,
        auth_client,
        config_entry,
        lambda entry, h: entry.start_reconfigure_flow(h),
        "reconfigure",
        "reconfigure_sms_code",
        "reconfigure_successful",
    )


async def _reauth_reconfigure_invalid_sms(
    hass: HomeAssistant,
    auth_client: MagicMock,
    config_entry: MockConfigEntry,
    flow_starter,
    expected_sms_step_id: str,
    expected_reason: str,
) -> None:
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await flow_starter(config_entry, hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PHONE_NUMBER: MOCK_PHONE_NUMBER},
    )

    auth_client.verify_phone_number.side_effect = FressnapfTrackerInvalidTokenError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_SMS_CODE: "999999"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(expected_sms_step_id)
    expect(result["errors"]).to_equal({"base": "invalid_sms_code"})

    auth_client.verify_phone_number.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_SMS_CODE: "0123456"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(expected_reason)


@test
async def reauth_flow_invalid_sms_code(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api_init: MagicMock = Depends(mock_api_client_init),
    _api_coord: MagicMock = Depends(mock_api_client_coordinator),
    auth_client: MagicMock = Depends(mock_auth_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow with invalid SMS code."""
    await _reauth_reconfigure_invalid_sms(
        hass,
        auth_client,
        config_entry,
        lambda entry, h: entry.start_reauth_flow(h),
        "reauth_sms_code",
        "reauth_successful",
    )


@test
async def reconfigure_flow_invalid_sms_code(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api_init: MagicMock = Depends(mock_api_client_init),
    _api_coord: MagicMock = Depends(mock_api_client_coordinator),
    auth_client: MagicMock = Depends(mock_auth_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow with invalid SMS code."""
    await _reauth_reconfigure_invalid_sms(
        hass,
        auth_client,
        config_entry,
        lambda entry, h: entry.start_reconfigure_flow(h),
        "reconfigure_sms_code",
        "reconfigure_successful",
    )


async def _reauth_reconfigure_invalid_user(
    hass: HomeAssistant,
    auth_client: MagicMock,
    config_entry: MockConfigEntry,
    flow_starter,
    expected_step_id: str,
    expected_sms_step_id: str,
    expected_reason: str,
) -> None:
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await flow_starter(config_entry, hass)

    auth_client.request_sms_code = AsyncMock(
        return_value=SmsCodeResponse(id=MOCK_USER_ID + 1)
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PHONE_NUMBER: f"{MOCK_PHONE_NUMBER}123"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(expected_step_id)
    expect(result["errors"]).to_equal({"base": "account_change_not_allowed"})

    auth_client.request_sms_code = AsyncMock(
        return_value=SmsCodeResponse(id=MOCK_USER_ID)
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PHONE_NUMBER: MOCK_PHONE_NUMBER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(expected_sms_step_id)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_SMS_CODE: "0123456"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(expected_reason)


@test
async def reauth_flow_invalid_user_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api_init: MagicMock = Depends(mock_api_client_init),
    _api_coord: MagicMock = Depends(mock_api_client_coordinator),
    auth_client: MagicMock = Depends(mock_auth_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow does not allow changing to another account."""
    await _reauth_reconfigure_invalid_user(
        hass,
        auth_client,
        config_entry,
        lambda entry, h: entry.start_reauth_flow(h),
        "reauth_confirm",
        "reauth_sms_code",
        "reauth_successful",
    )


@test
async def reconfigure_flow_invalid_user_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api_init: MagicMock = Depends(mock_api_client_init),
    _api_coord: MagicMock = Depends(mock_api_client_coordinator),
    auth_client: MagicMock = Depends(mock_auth_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow does not allow changing to another account."""
    await _reauth_reconfigure_invalid_user(
        hass,
        auth_client,
        config_entry,
        lambda entry, h: entry.start_reconfigure_flow(h),
        "reconfigure",
        "reconfigure_sms_code",
        "reconfigure_successful",
    )
