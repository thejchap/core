"""Test the Read Your Meter Pro config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.rympro.config_flow import (
    CannotConnectError,
    UnauthorizedError,
)
from homeassistant.components.rympro.const import DOMAIN
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TOKEN, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_DATA = {
    CONF_EMAIL: "test-email",
    CONF_PASSWORD: "test-password",
    CONF_TOKEN: "test-token",
    CONF_UNIQUE_ID: "test-account-number",
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch(
            "homeassistant.components.rympro.config_flow.RymPro.login",
            return_value="test-token",
        ),
        patch(
            "homeassistant.components.rympro.config_flow.RymPro.account_info",
            return_value={"accountNumber": TEST_DATA[CONF_UNIQUE_ID]},
        ),
        patch(
            "homeassistant.components.rympro.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: TEST_DATA[CONF_EMAIL],
                CONF_PASSWORD: TEST_DATA[CONF_PASSWORD],
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(TEST_DATA[CONF_EMAIL])
    expect(result2["data"]).to_equal(TEST_DATA)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", exception=UnauthorizedError, error="invalid_auth"),
    test.case("cannot_connect", exception=CannotConnectError, error="cannot_connect"),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def login_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    exception: type[Exception],
    error: str,
) -> None:
    """Test we handle config flow errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "homeassistant.components.rympro.config_flow.RymPro.login",
        side_effect=exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: TEST_DATA[CONF_EMAIL],
                CONF_PASSWORD: TEST_DATA[CONF_PASSWORD],
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": error})

    with (
        patch(
            "homeassistant.components.rympro.config_flow.RymPro.login",
            return_value="test-token",
        ),
        patch(
            "homeassistant.components.rympro.config_flow.RymPro.account_info",
            return_value={"accountNumber": TEST_DATA[CONF_UNIQUE_ID]},
        ),
        patch(
            "homeassistant.components.rympro.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_EMAIL: TEST_DATA[CONF_EMAIL],
                CONF_PASSWORD: TEST_DATA[CONF_PASSWORD],
            },
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal(TEST_DATA[CONF_EMAIL])
    expect(result3["data"]).to_equal(TEST_DATA)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that a flow with an existing account aborts."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch(
            "homeassistant.components.rympro.config_flow.RymPro.login",
            return_value="test-token",
        ),
        patch(
            "homeassistant.components.rympro.config_flow.RymPro.account_info",
            return_value={"accountNumber": TEST_DATA[CONF_UNIQUE_ID]},
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: TEST_DATA[CONF_EMAIL],
                CONF_PASSWORD: TEST_DATA[CONF_PASSWORD],
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def form_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauthentication."""
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch(
            "homeassistant.components.rympro.config_flow.RymPro.login",
            return_value="test-token",
        ),
        patch(
            "homeassistant.components.rympro.config_flow.RymPro.account_info",
            return_value={"accountNumber": TEST_DATA[CONF_UNIQUE_ID]},
        ),
        patch(
            "homeassistant.components.rympro.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: TEST_DATA[CONF_EMAIL],
                CONF_PASSWORD: "new_password",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new_password")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_reauth_with_new_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauthentication with new account."""
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch(
            "homeassistant.components.rympro.config_flow.RymPro.login",
            return_value="test-token",
        ),
        patch(
            "homeassistant.components.rympro.config_flow.RymPro.account_info",
            return_value={"accountNumber": "new-account-number"},
        ),
        patch(
            "homeassistant.components.rympro.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: TEST_DATA[CONF_EMAIL],
                CONF_PASSWORD: TEST_DATA[CONF_PASSWORD],
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_UNIQUE_ID]).to_equal("new-account-number")
    expect(config_entry.unique_id).to_equal("new-account-number")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
