"""Tests Config flow for the Redgtech integration."""

from __future__ import annotations

from unittest.mock import MagicMock

from redgtech_api.api import RedgtechAuthError, RedgtechConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.redgtech.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_redgtech_api as mock_redgtech_api_fx

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "123456"
FAKE_TOKEN = "fake_token"


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test.cases(
    test.case("invalid_auth", side_effect=RedgtechAuthError, expected_error="invalid_auth"),
    test.case(
        "cannot_connect",
        side_effect=RedgtechConnectionError,
        expected_error="cannot_connect",
    ),
    test.case(
        "unknown", side_effect=Exception("Generic error"), expected_error="unknown"
    ),
)
async def user_step_errors(
    *,
    side_effect: type[Exception] | Exception,
    expected_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    api: MagicMock = Depends(mock_redgtech_api_fx),
) -> None:
    """Test user step with various errors."""
    user_input = {CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD}
    api.login.side_effect = side_effect
    api.login.return_value = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=user_input
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal(expected_error)
    api.login.assert_called_once_with(TEST_EMAIL, TEST_PASSWORD)


@test
async def user_step_creates_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    api: MagicMock = Depends(mock_redgtech_api_fx),
) -> None:
    """Test the correct creation of the entry in the configuration."""
    user_input = {CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD}
    api.login.reset_mock()
    api.login.return_value = FAKE_TOKEN
    api.login.side_effect = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=user_input
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_EMAIL)
    expect(result["data"]).to_equal(user_input)
    api.login.assert_any_call(TEST_EMAIL, TEST_PASSWORD)


@test
async def user_step_duplicate_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    api: MagicMock = Depends(mock_redgtech_api_fx),
) -> None:
    """Test attempt to add duplicate entry."""
    existing = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_EMAIL,
        data={CONF_EMAIL: TEST_EMAIL},
    )
    existing.add_to_hass(hass)

    user_input = {CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=user_input
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    api.login.assert_not_called()


@test.cases(
    test.case("invalid_auth", side_effect=RedgtechAuthError, expected_error="invalid_auth"),
    test.case(
        "cannot_connect",
        side_effect=RedgtechConnectionError,
        expected_error="cannot_connect",
    ),
    test.case(
        "unknown", side_effect=Exception("Generic error"), expected_error="unknown"
    ),
)
async def user_step_error_recovery(
    *,
    side_effect: type[Exception] | Exception,
    expected_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    api: MagicMock = Depends(mock_redgtech_api_fx),
) -> None:
    """Test that the flow can recover from errors and complete successfully."""
    user_input = {CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD}

    api.login.reset_mock()
    api.login.return_value = None
    api.login.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=user_input
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal(expected_error)
    expect(api.login.call_count >= 1).to_be(True)
    first_call_count = api.login.call_count

    api.login.side_effect = None
    api.login.return_value = FAKE_TOKEN
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=user_input
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_EMAIL)
    expect(result["data"]).to_equal(user_input)
    expect(api.login.call_count > first_call_count).to_be(True)
