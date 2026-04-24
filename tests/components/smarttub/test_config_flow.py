"""Test the smarttub config flow."""

from __future__ import annotations

from unittest.mock import MagicMock

from smarttub import LoginFailed
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.smarttub.const import DOMAIN
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import account, config_entry, mock_setup_entry, smarttub_api

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _api: MagicMock = Depends(smarttub_api),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    account_mock: MagicMock = Depends(account),
) -> None:
    """Test the user config flow creates an entry with correct data."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "test-email", CONF_PASSWORD: "test-password"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test-email")
    expect(result["data"]).to_equal(
        {
            CONF_EMAIL: "test-email",
            CONF_PASSWORD: "test-password",
        }
    )
    expect(result["result"].unique_id).to_equal(account_mock.id)
    setup_entry.assert_called_once()


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api: MagicMock = Depends(smarttub_api),
    _setup_entry: MagicMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle invalid auth and can recover."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    api.login.side_effect = LoginFailed

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "test-email", CONF_PASSWORD: "test-password"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    api.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "test-email", CONF_PASSWORD: "test-password"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def reauth_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: MagicMock = Depends(smarttub_api),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test reauthentication flow."""
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "test-email3", CONF_PASSWORD: "test-password3"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data[CONF_EMAIL]).to_equal("test-email3")
    expect(entry.data[CONF_PASSWORD]).to_equal("test-password3")


@test
async def reauth_wrong_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: MagicMock = Depends(smarttub_api),
    account_mock: MagicMock = Depends(account),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test reauth flow if user enters credentials for a different account."""
    entry.add_to_hass(hass)

    mock_entry2 = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_EMAIL: "test-email2", CONF_PASSWORD: "test-password2"},
        unique_id="mockaccount2",
    )
    mock_entry2.add_to_hass(hass)

    account_mock.id = entry.unique_id
    result = await mock_entry2.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "test-email1", CONF_PASSWORD: "test-password1"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
