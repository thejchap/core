"""Test the Cync config flow."""

from unittest.mock import ANY, AsyncMock, MagicMock

from pycync.exceptions import AuthFailedError, CyncError, TwoFactorRequiredError
from tryke import Depends, expect, fixture, test

from homeassistant.components.cync.const import (
    CONF_AUTHORIZE_STRING,
    CONF_EXPIRES_AT,
    CONF_REFRESH_TOKEN,
    CONF_TWO_FACTOR_CODE,
    CONF_USER_ID,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import auth_client, cync_client, mock_config_entry, mock_setup_entry
from .const import MOCKED_EMAIL, MOCKED_USER, SECOND_MOCKED_USER

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _auth: AsyncMock = Depends(auth_client),
    _cync: AsyncMock = Depends(cync_client),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form_auth_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that an auth flow without two factor succeeds."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: MOCKED_EMAIL,
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MOCKED_EMAIL)
    expect(dict(result["data"])).to_equal(
        {
            CONF_USER_ID: MOCKED_USER.user_id,
            CONF_AUTHORIZE_STRING: "test_authorize_string",
            CONF_EXPIRES_AT: ANY,
            CONF_ACCESS_TOKEN: "test_token",
            CONF_REFRESH_TOKEN: "test_refresh_token",
        }
    )
    expect(result["result"].unique_id).to_equal(str(MOCKED_USER.user_id))
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_two_factor_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    auth: MagicMock = Depends(auth_client),
) -> None:
    """Test we handle a request for a two factor code."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    auth.login.side_effect = TwoFactorRequiredError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: MOCKED_EMAIL,
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("two_factor")

    auth.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TWO_FACTOR_CODE: "123456"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MOCKED_EMAIL)
    expect(dict(result["data"])).to_equal(
        {
            CONF_USER_ID: MOCKED_USER.user_id,
            CONF_AUTHORIZE_STRING: "test_authorize_string",
            CONF_EXPIRES_AT: ANY,
            CONF_ACCESS_TOKEN: "test_token",
            CONF_REFRESH_TOKEN: "test_refresh_token",
        }
    )
    expect(result["result"].unique_id).to_equal(str(MOCKED_USER.user_id))
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_reauth_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    auth: MagicMock = Depends(auth_client),
) -> None:
    """Test we handle re-authentication with two-factor."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")

    auth.login.side_effect = TwoFactorRequiredError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: MOCKED_EMAIL,
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("two_factor")

    auth.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TWO_FACTOR_CODE: "123456"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(dict(config_entry.data)).to_equal(
        {
            CONF_USER_ID: MOCKED_USER.user_id,
            CONF_AUTHORIZE_STRING: "test_authorize_string",
            CONF_EXPIRES_AT: ANY,
            CONF_ACCESS_TOKEN: "test_token",
            CONF_REFRESH_TOKEN: "test_refresh_token",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_reauth_unique_id_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    auth: MagicMock = Depends(auth_client),
) -> None:
    """Test we handle a unique ID mismatch when re-authenticating."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")

    auth.user = SECOND_MOCKED_USER
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: MOCKED_EMAIL,
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")


@test
async def form_unique_id_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that setting up a config with a unique ID that already exists fails."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: MOCKED_EMAIL,
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("invalid_auth", error_type=AuthFailedError, error_string="invalid_auth"),
    test.case("cannot_connect", error_type=CyncError, error_string="cannot_connect"),
    test.case("unknown", error_type=Exception, error_string="unknown"),
)
async def form_two_factor_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    auth: MagicMock = Depends(auth_client),
    *,
    error_type: Exception,
    error_string: str,
) -> None:
    """Test we handle a request for a two factor code with errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    auth.login.side_effect = TwoFactorRequiredError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: MOCKED_EMAIL,
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("two_factor")

    auth.login.side_effect = error_type
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TWO_FACTOR_CODE: "123456"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_string})
    expect(result["step_id"]).to_equal("user")

    auth.login.side_effect = TwoFactorRequiredError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: MOCKED_EMAIL,
            CONF_PASSWORD: "test-password",
        },
    )

    auth.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TWO_FACTOR_CODE: "567890"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MOCKED_EMAIL)
    expect(dict(result["data"])).to_equal(
        {
            CONF_USER_ID: MOCKED_USER.user_id,
            CONF_AUTHORIZE_STRING: "test_authorize_string",
            CONF_EXPIRES_AT: ANY,
            CONF_ACCESS_TOKEN: "test_token",
            CONF_REFRESH_TOKEN: "test_refresh_token",
        }
    )
    expect(result["result"].unique_id).to_equal(str(MOCKED_USER.user_id))
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", error_type=AuthFailedError, error_string="invalid_auth"),
    test.case("cannot_connect", error_type=CyncError, error_string="cannot_connect"),
    test.case("unknown", error_type=Exception, error_string="unknown"),
)
async def form_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    auth: MagicMock = Depends(auth_client),
    *,
    error_type: Exception,
    error_string: str,
) -> None:
    """Test we handle errors in the user step of the setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    auth.login.side_effect = error_type
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: MOCKED_EMAIL,
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_string})
    expect(result["step_id"]).to_equal("user")

    auth.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: MOCKED_EMAIL,
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MOCKED_EMAIL)
    expect(dict(result["data"])).to_equal(
        {
            CONF_USER_ID: MOCKED_USER.user_id,
            CONF_AUTHORIZE_STRING: "test_authorize_string",
            CONF_EXPIRES_AT: ANY,
            CONF_ACCESS_TOKEN: "test_token",
            CONF_REFRESH_TOKEN: "test_refresh_token",
        }
    )
    expect(result["result"].unique_id).to_equal(str(MOCKED_USER.user_id))
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", error_type=AuthFailedError, error_string="invalid_auth"),
    test.case("cannot_connect", error_type=CyncError, error_string="cannot_connect"),
    test.case("unknown", error_type=Exception, error_string="unknown"),
)
async def form_reauth_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    auth: MagicMock = Depends(auth_client),
    *,
    error_type: Exception,
    error_string: str,
) -> None:
    """Test we handle errors in the reauth flow."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")

    auth.login.side_effect = error_type
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: MOCKED_EMAIL,
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_string})
    expect(result["step_id"]).to_equal("reauth_confirm")

    auth.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: MOCKED_EMAIL,
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(dict(config_entry.data)).to_equal(
        {
            CONF_USER_ID: MOCKED_USER.user_id,
            CONF_AUTHORIZE_STRING: "test_authorize_string",
            CONF_EXPIRES_AT: ANY,
            CONF_ACCESS_TOKEN: "test_token",
            CONF_REFRESH_TOKEN: "test_refresh_token",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)
