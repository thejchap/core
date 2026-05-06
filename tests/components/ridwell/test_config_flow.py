"""Test the Ridwell config flow."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

from aioridwell.errors import InvalidCredentialsError, RidwellError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.ridwell.const import (
    CALENDAR_TITLE_ROTATING,
    CONF_CALENDAR_TITLE,
    DOMAIN,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    TEST_PASSWORD,
    TEST_USERNAME,
    config as config_fx,
    config_entry as config_entry_fx,
    mock_aioridwell as mock_aioridwell_fx,
    setup_config_entry as setup_config_entry_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test.cases(
    test.case(
        "invalid_auth",
        get_client_response=AsyncMock(side_effect=InvalidCredentialsError),
        errors={"base": "invalid_auth"},
    ),
    test.case(
        "unknown",
        get_client_response=AsyncMock(side_effect=RidwellError),
        errors={"base": "unknown"},
    ),
)
async def create_entry(
    *,
    get_client_response: AsyncMock,
    errors: dict[str, str],
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(config_fx),
    _mock: None = Depends(mock_aioridwell_fx),
) -> None:
    """Test creating an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.ridwell.config_flow.async_get_client",
        get_client_response,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=config
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal(errors)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=config
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_USERNAME)
    expect(result["data"]).to_equal(
        {CONF_USERNAME: TEST_USERNAME, CONF_PASSWORD: TEST_PASSWORD}
    )


@test
async def duplicate_error(
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(config_fx),
    _setup: None = Depends(setup_config_entry_fx),
) -> None:
    """Test that errors are shown when duplicate entries are added."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=config
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def step_reauth(
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(config_fx),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    _setup: None = Depends(setup_config_entry_fx),
) -> None:
    """Test a full reauth flow."""
    result = await config_entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "new_password"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new_password")
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def option_flow_event_title(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
) -> None:
    """Test option flow for event title."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_CALENDAR_TITLE: CALENDAR_TITLE_ROTATING},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_CALENDAR_TITLE]).to_equal(CALENDAR_TITLE_ROTATING)


@test
async def successful_config_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(config_fx),
    _mock: None = Depends(mock_aioridwell_fx),
) -> None:
    """Test the happy path of a successful config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=config
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_USERNAME)
    expect(result["data"]).to_equal(config)
