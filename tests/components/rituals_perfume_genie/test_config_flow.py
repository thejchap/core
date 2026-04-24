"""Test the Rituals Perfume Genie config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from aiohttp import ClientError
from pyrituals import AuthenticationException
from tryke import Depends, expect, fixture, test

from homeassistant.components.rituals_perfume_genie.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_rituals_account as mock_rituals_account_fx,
    mock_setup_entry as mock_setup_entry_fx,
)
from .const import TEST_EMAIL, TEST_PASSWORD

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def user_flow_success(
    hass: HomeAssistant = Depends(hass_fixture),
    _rituals: AsyncMock = Depends(mock_rituals_account_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test successful user flow setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_EMAIL)
    expect(result["data"]).to_equal(
        {CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD}
    )
    expect(result["result"].unique_id).to_equal(TEST_EMAIL)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", exception=AuthenticationException, error="invalid_auth"),
    test.case("cannot_connect", exception=ClientError, error="cannot_connect"),
)
async def user_flow_errors(
    *,
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    rituals: AsyncMock = Depends(mock_rituals_account_fx),
    _mse: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test user flow with different errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    rituals.authenticate.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    rituals.authenticate.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def duplicate_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    _rituals: AsyncMock = Depends(mock_rituals_account_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test user flow with invalid credentials."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_flow_success(
    hass: HomeAssistant = Depends(hass_fixture),
    _rituals: AsyncMock = Depends(mock_rituals_account_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test successful reauth flow (updating credentials)."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new_correct_password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data[CONF_PASSWORD]).to_equal("new_correct_password")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", exception=AuthenticationException, error="invalid_auth"),
    test.case("cannot_connect", exception=ClientError, error="cannot_connect"),
)
async def reauth_flow_errors(
    *,
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    rituals: AsyncMock = Depends(mock_rituals_account_fx),
    _mse: AsyncMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reauth flow with different errors."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)

    rituals.authenticate.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new_correct_password"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    rituals.authenticate.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new_correct_password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data[CONF_PASSWORD]).to_equal("new_correct_password")


@test
async def reauth_migrated_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    _rituals: AsyncMock = Depends(mock_rituals_account_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test successful reauth flow (updating credentials)."""
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_EMAIL,
        data={},
        title=TEST_EMAIL,
        version=2,
    )
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new_correct_password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data).to_equal(
        {CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: "new_correct_password"}
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
