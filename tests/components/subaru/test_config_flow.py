"""Tests for the Subaru component config flow."""

from copy import deepcopy
from unittest import mock
from unittest.mock import PropertyMock, patch

from subarulink.exceptions import InvalidCredentials, InvalidPIN, SubaruException
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.subaru import config_flow
from homeassistant.components.subaru.const import CONF_UPDATE_ENABLED, DOMAIN
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_DEVICE_ID, CONF_PIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from .conftest import (
    MOCK_API_2FA_CONTACTS,
    MOCK_API_2FA_REQUEST,
    MOCK_API_2FA_VERIFY,
    MOCK_API_CONNECT,
    MOCK_API_DEVICE_REGISTERED,
    MOCK_API_IS_PIN_REQUIRED,
    MOCK_API_TEST_PIN,
    MOCK_API_UPDATE_SAVED_PIN,
    TEST_CONFIG,
    TEST_CREDS,
    TEST_DEVICE_ID,
    TEST_PIN,
    TEST_USERNAME,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

ASYNC_SETUP_ENTRY = "homeassistant.components.subaru.async_setup_entry"
MOCK_2FA_CONTACTS = {
    "phone": "123-123-1234",
    "userName": "email@addr.com",
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


async def _init_user_form(hass: HomeAssistant) -> ConfigFlowResult:
    """Return initial form for Subaru config flow."""
    return await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def _advance_two_factor_start(
    hass: HomeAssistant, flow_id: str
) -> ConfigFlowResult:
    with (
        patch(MOCK_API_CONNECT, return_value=True),
        patch(MOCK_API_2FA_CONTACTS, new_callable=PropertyMock) as mock_contacts,
    ):
        mock_contacts.return_value = MOCK_2FA_CONTACTS
        return await hass.config_entries.flow.async_configure(
            flow_id, user_input=TEST_CREDS
        )


async def _advance_two_factor_verify(
    hass: HomeAssistant, flow_id: str
) -> ConfigFlowResult:
    with (
        patch(MOCK_API_2FA_REQUEST, return_value=True),
        patch(MOCK_API_2FA_CONTACTS, new_callable=PropertyMock) as mock_contacts,
    ):
        mock_contacts.return_value = MOCK_2FA_CONTACTS
        return await hass.config_entries.flow.async_configure(
            flow_id,
            user_input={config_flow.CONF_CONTACT_METHOD: "email@addr.com"},
        )


async def _advance_pin(hass: HomeAssistant, flow_id: str) -> ConfigFlowResult:
    with (
        patch(MOCK_API_2FA_VERIFY, return_value=True),
        patch(MOCK_API_IS_PIN_REQUIRED, return_value=True),
    ):
        return await hass.config_entries.flow.async_configure(
            flow_id,
            user_input={config_flow.CONF_VALIDATION_CODE: "123456"},
        )


async def _init_options_form(hass: HomeAssistant) -> ConfigFlowResult:
    entry = MockConfigEntry(domain=DOMAIN, data={}, options=None)
    entry.add_to_hass(hass)
    await async_setup_component(hass, DOMAIN, {})
    return await hass.config_entries.options.async_init(entry.entry_id)


@test
async def user_form_init(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the initial user form for first step of the config flow."""
    form = await _init_user_form(hass)
    expect(form["description_placeholders"]).to_be(None)
    expect(form["errors"]).to_be(None)
    expect(form["handler"]).to_equal(DOMAIN)
    expect(form["step_id"]).to_equal("user")
    expect(form["type"]).to_be(FlowResultType.FORM)


@test
async def user_form_repeat_identifier(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle repeat identifiers."""
    form = await _init_user_form(hass)
    entry = MockConfigEntry(
        domain=DOMAIN, title=TEST_USERNAME, data=TEST_CREDS, options=None
    )
    entry.add_to_hass(hass)

    with patch(MOCK_API_CONNECT, return_value=True) as mock_connect:
        result = await hass.config_entries.flow.async_configure(
            form["flow_id"],
            TEST_CREDS,
        )
    expect(len(mock_connect.mock_calls)).to_equal(0)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    form = await _init_user_form(hass)
    with patch(MOCK_API_CONNECT, side_effect=SubaruException(None)) as mock_connect:
        result = await hass.config_entries.flow.async_configure(
            form["flow_id"],
            TEST_CREDS,
        )
    expect(len(mock_connect.mock_calls)).to_equal(1)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def user_form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth."""
    form = await _init_user_form(hass)
    with patch(
        MOCK_API_CONNECT, side_effect=InvalidCredentials("invalidAccount")
    ) as mock_connect:
        result = await hass.config_entries.flow.async_configure(
            form["flow_id"],
            TEST_CREDS,
        )
    expect(len(mock_connect.mock_calls)).to_equal(1)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})


@test
async def user_form_pin_not_required(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful login when no PIN is required."""
    form = await _init_user_form(hass)
    form = await _advance_two_factor_start(hass, form["flow_id"])
    form = await _advance_two_factor_verify(hass, form["flow_id"])

    with (
        patch(MOCK_API_2FA_VERIFY, return_value=True) as mock_two_factor_verify,
        patch(MOCK_API_IS_PIN_REQUIRED, return_value=False) as mock_is_pin_required,
        patch(ASYNC_SETUP_ENTRY, return_value=True) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            form["flow_id"],
            user_input={config_flow.CONF_VALIDATION_CODE: "123456"},
        )
    expect(len(mock_two_factor_verify.mock_calls)).to_equal(1)
    expect(len(mock_is_pin_required.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    expected = {
        "context": {"source": "user"},
        "title": TEST_USERNAME,
        "description": None,
        "description_placeholders": None,
        "flow_id": mock.ANY,
        "result": mock.ANY,
        "handler": DOMAIN,
        "type": "create_entry",
        "version": 1,
        "data": deepcopy(TEST_CONFIG),
        "options": {},
        "minor_version": 1,
        "subentries": (),
    }

    expected["data"][CONF_PIN] = None
    result["data"][CONF_DEVICE_ID] = TEST_DEVICE_ID
    expect(result).to_equal(expected)


@test
async def registered_pin_required(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if the device is already registered and PIN required."""
    form = await _init_user_form(hass)
    with (
        patch(MOCK_API_CONNECT, return_value=True),
        patch(
            MOCK_API_DEVICE_REGISTERED, new_callable=PropertyMock
        ) as mock_device_registered,
        patch(MOCK_API_IS_PIN_REQUIRED, return_value=True),
    ):
        mock_device_registered.return_value = True
        await hass.config_entries.flow.async_configure(
            form["flow_id"], user_input=TEST_CREDS
        )


@test
async def registered_no_pin_required(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if the device is already registered and PIN not required."""
    form = await _init_user_form(hass)
    with (
        patch(MOCK_API_CONNECT, return_value=True),
        patch(
            MOCK_API_DEVICE_REGISTERED, new_callable=PropertyMock
        ) as mock_device_registered,
        patch(MOCK_API_IS_PIN_REQUIRED, return_value=False),
    ):
        mock_device_registered.return_value = True
        await hass.config_entries.flow.async_configure(
            form["flow_id"], user_input=TEST_CREDS
        )


@test
async def two_factor_request_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test two factor contact method selection."""
    form = await _init_user_form(hass)
    form = await _advance_two_factor_start(hass, form["flow_id"])
    with (
        patch(MOCK_API_2FA_REQUEST, return_value=True) as mock_two_factor_request,
        patch(MOCK_API_2FA_CONTACTS, new_callable=PropertyMock) as mock_contacts,
    ):
        mock_contacts.return_value = MOCK_2FA_CONTACTS
        await hass.config_entries.flow.async_configure(
            form["flow_id"],
            user_input={config_flow.CONF_CONTACT_METHOD: "email@addr.com"},
        )
    expect(len(mock_two_factor_request.mock_calls)).to_equal(1)


@test
async def two_factor_request_fail(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test two factor auth request failure."""
    form = await _init_user_form(hass)
    form = await _advance_two_factor_start(hass, form["flow_id"])
    with (
        patch(MOCK_API_2FA_REQUEST, return_value=False) as mock_two_factor_request,
        patch(MOCK_API_2FA_CONTACTS, new_callable=PropertyMock) as mock_contacts,
    ):
        mock_contacts.return_value = MOCK_2FA_CONTACTS
        result = await hass.config_entries.flow.async_configure(
            form["flow_id"],
            user_input={config_flow.CONF_CONTACT_METHOD: "email@addr.com"},
        )
    expect(len(mock_two_factor_request.mock_calls)).to_equal(1)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("two_factor_request_failed")


@test
async def two_factor_verify_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test two factor verification."""
    form = await _init_user_form(hass)
    form = await _advance_two_factor_start(hass, form["flow_id"])
    form = await _advance_two_factor_verify(hass, form["flow_id"])
    with (
        patch(MOCK_API_2FA_VERIFY, return_value=True) as mock_two_factor_verify,
        patch(MOCK_API_IS_PIN_REQUIRED, return_value=True) as mock_is_in_required,
    ):
        await hass.config_entries.flow.async_configure(
            form["flow_id"],
            user_input={config_flow.CONF_VALIDATION_CODE: "123456"},
        )
    expect(len(mock_two_factor_verify.mock_calls)).to_equal(1)
    expect(len(mock_is_in_required.mock_calls)).to_equal(1)


@test
async def two_factor_verify_bad_format(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test two factor verification bad format."""
    form = await _init_user_form(hass)
    form = await _advance_two_factor_start(hass, form["flow_id"])
    form = await _advance_two_factor_verify(hass, form["flow_id"])
    with (
        patch(MOCK_API_2FA_VERIFY, return_value=False) as mock_two_factor_verify,
        patch(MOCK_API_IS_PIN_REQUIRED, return_value=True) as mock_is_pin_required,
    ):
        result = await hass.config_entries.flow.async_configure(
            form["flow_id"],
            user_input={config_flow.CONF_VALIDATION_CODE: "1234567"},
        )
    expect(len(mock_two_factor_verify.mock_calls)).to_equal(0)
    expect(len(mock_is_pin_required.mock_calls)).to_equal(0)
    expect(result["errors"]).to_equal({"base": "bad_validation_code_format"})


@test
async def two_factor_verify_fail(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test two factor verification failure."""
    form = await _init_user_form(hass)
    form = await _advance_two_factor_start(hass, form["flow_id"])
    form = await _advance_two_factor_verify(hass, form["flow_id"])
    with (
        patch(MOCK_API_2FA_VERIFY, return_value=False) as mock_two_factor_verify,
        patch(MOCK_API_IS_PIN_REQUIRED, return_value=True) as mock_is_pin_required,
    ):
        result = await hass.config_entries.flow.async_configure(
            form["flow_id"],
            user_input={config_flow.CONF_VALIDATION_CODE: "123456"},
        )
    expect(len(mock_two_factor_verify.mock_calls)).to_equal(1)
    expect(len(mock_is_pin_required.mock_calls)).to_equal(0)
    expect(result["errors"]).to_equal({"base": "incorrect_validation_code"})


@test
async def pin_form_init(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the pin entry form for second step of the config flow."""
    form = await _init_user_form(hass)
    form = await _advance_two_factor_start(hass, form["flow_id"])
    form = await _advance_two_factor_verify(hass, form["flow_id"])
    form = await _advance_pin(hass, form["flow_id"])
    expected = {
        "data_schema": config_flow.PIN_SCHEMA,
        "description_placeholders": None,
        "errors": None,
        "flow_id": mock.ANY,
        "handler": DOMAIN,
        "step_id": "pin",
        "type": "form",
        "last_step": None,
        "preview": None,
    }
    expect(form).to_equal(expected)


@test
async def pin_form_bad_pin_format(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid pin."""
    form = await _init_user_form(hass)
    form = await _advance_two_factor_start(hass, form["flow_id"])
    form = await _advance_two_factor_verify(hass, form["flow_id"])
    form = await _advance_pin(hass, form["flow_id"])
    with (
        patch(MOCK_API_TEST_PIN) as mock_test_pin,
        patch(MOCK_API_UPDATE_SAVED_PIN, return_value=True) as mock_update_saved_pin,
    ):
        result = await hass.config_entries.flow.async_configure(
            form["flow_id"], user_input={CONF_PIN: "abcd"}
        )
    expect(len(mock_test_pin.mock_calls)).to_equal(0)
    expect(len(mock_update_saved_pin.mock_calls)).to_equal(1)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "bad_pin_format"})


@test
async def pin_form_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful PIN entry."""
    form = await _init_user_form(hass)
    form = await _advance_two_factor_start(hass, form["flow_id"])
    form = await _advance_two_factor_verify(hass, form["flow_id"])
    form = await _advance_pin(hass, form["flow_id"])
    with (
        patch(MOCK_API_TEST_PIN, return_value=True) as mock_test_pin,
        patch(MOCK_API_UPDATE_SAVED_PIN, return_value=True) as mock_update_saved_pin,
        patch(ASYNC_SETUP_ENTRY, return_value=True) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            form["flow_id"], user_input={CONF_PIN: TEST_PIN}
        )

    expect(len(mock_test_pin.mock_calls)).to_equal(1)
    expect(len(mock_update_saved_pin.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expected = {
        "context": {"source": "user"},
        "title": TEST_USERNAME,
        "description": None,
        "description_placeholders": None,
        "flow_id": mock.ANY,
        "result": mock.ANY,
        "handler": DOMAIN,
        "type": "create_entry",
        "version": 1,
        "data": TEST_CONFIG,
        "options": {},
        "minor_version": 1,
        "subentries": (),
    }
    result["data"][CONF_DEVICE_ID] = TEST_DEVICE_ID
    expect(result).to_equal(expected)


@test
async def pin_form_incorrect_pin(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid pin."""
    form = await _init_user_form(hass)
    form = await _advance_two_factor_start(hass, form["flow_id"])
    form = await _advance_two_factor_verify(hass, form["flow_id"])
    form = await _advance_pin(hass, form["flow_id"])
    with (
        patch(MOCK_API_TEST_PIN, side_effect=InvalidPIN("invalidPin")) as mock_test_pin,
        patch(MOCK_API_UPDATE_SAVED_PIN, return_value=True) as mock_update_saved_pin,
    ):
        result = await hass.config_entries.flow.async_configure(
            form["flow_id"], user_input={CONF_PIN: TEST_PIN}
        )
    expect(len(mock_test_pin.mock_calls)).to_equal(1)
    expect(len(mock_update_saved_pin.mock_calls)).to_equal(1)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "incorrect_pin"})


@test
async def option_flow_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options form."""
    form = await _init_options_form(hass)
    expect(form["description_placeholders"]).to_be(None)
    expect(form["errors"]).to_be(None)
    expect(form["step_id"]).to_equal("init")
    expect(form["type"]).to_be(FlowResultType.FORM)


@test
async def option_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options."""
    form = await _init_options_form(hass)
    result = await hass.config_entries.options.async_configure(
        form["flow_id"],
        user_input={
            CONF_UPDATE_ENABLED: False,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_UPDATE_ENABLED: False,
        }
    )
