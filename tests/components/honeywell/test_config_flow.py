"""Tests for honeywell config flow."""

from unittest.mock import MagicMock, patch

import aiosomecomfort
from tryke import Depends, expect, fixture, test

from homeassistant.components.honeywell.const import (
    CONF_COOL_AWAY_TEMPERATURE,
    CONF_HEAT_AWAY_TEMPERATURE,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import client, config_entry as config_entry_fx

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

FAKE_CONFIG = {
    "username": "fake",
    "password": "user",
    "away_cool_temperature": 88,
    "away_heat_temperature": 61,
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _client: MagicMock = Depends(client),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def show_authenticate_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the config form is shown."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api_client: MagicMock = Depends(client),
) -> None:
    """Test that an error message is shown on connection fail."""
    api_client.login.side_effect = aiosomecomfort.device.ConnectionError
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=FAKE_CONFIG
    )
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def auth_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api_client: MagicMock = Depends(client),
) -> None:
    """Test that an error message is shown on login fail."""
    api_client.login.side_effect = aiosomecomfort.device.AuthError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=FAKE_CONFIG
    )
    expect(result["errors"]).to_equal({"base": "invalid_auth"})


@test
async def create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the config entry is created."""
    with patch(
        "homeassistant.components.honeywell.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=FAKE_CONFIG
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(FAKE_CONFIG)


@test
async def show_option_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
) -> None:
    """Test that the option form is shown."""
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    with patch(
        "homeassistant.components.honeywell.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")


@test
async def create_option_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
) -> None:
    """Test that the config entry is created."""
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    with patch(
        "homeassistant.components.honeywell.async_setup_entry",
        return_value=True,
    ):
        options_form = await hass.config_entries.options.async_init(
            config_entry.entry_id
        )
        result = await hass.config_entries.options.async_configure(
            options_form["flow_id"],
            user_input={CONF_COOL_AWAY_TEMPERATURE: 1, CONF_HEAT_AWAY_TEMPERATURE: 2},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal(
        {
            CONF_COOL_AWAY_TEMPERATURE: 1,
            CONF_HEAT_AWAY_TEMPERATURE: 2,
        }
    )


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a successful reauth flow."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: "test-username", CONF_PASSWORD: "test-password"},
        unique_id="test-username",
    )
    mock_entry.add_to_hass(hass)
    result = await mock_entry.start_reauth_flow(hass)

    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.honeywell.async_setup_entry",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "new-username", CONF_PASSWORD: "new-password"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(mock_entry.data).to_equal(
        {
            CONF_USERNAME: "new-username",
            CONF_PASSWORD: "new-password",
        }
    )


@test
async def reauth_flow_auth_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api_client: MagicMock = Depends(client),
) -> None:
    """Test an authorization error reauth flow."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: "test-username", CONF_PASSWORD: "test-password"},
        unique_id="test-username",
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reauth_flow(hass)

    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    api_client.login.side_effect = aiosomecomfort.device.AuthError
    with patch(
        "homeassistant.components.honeywell.async_setup_entry",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "new-username", CONF_PASSWORD: "new-password"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test.cases(
    test.case("connection_error", error=aiosomecomfort.device.ConnectionError),
    test.case("connection_timeout", error=aiosomecomfort.device.ConnectionTimeout),
    test.case("timeout_error", error=TimeoutError),
)
async def reauth_flow_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api_client: MagicMock = Depends(client),
    *,
    error: type[Exception],
) -> None:
    """Test a connection error reauth flow."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: "test-username", CONF_PASSWORD: "test-password"},
        unique_id="test-username",
    )
    mock_entry.add_to_hass(hass)
    result = await mock_entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    api_client.login.side_effect = error

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "new-username", CONF_PASSWORD: "new-password"},
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})
