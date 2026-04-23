"""Tests for the NYT Games config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from nyt_games import NYTGamesAuthenticationError, NYTGamesError
from tryke import Depends, expect, fixture, test

from homeassistant.components.nyt_games.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.nyt_games._fixtures import (
    mock_config_entry,
    mock_nyt_games_client,
    mock_setup_entry,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Wire mock_network + mock_setup_entry for every test."""


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_nyt_games_client),
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TOKEN: "token"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("NYT Games")
    expect(result["data"]).to_equal({CONF_TOKEN: "token"})
    expect(result["result"].unique_id).to_equal("218886794")


@test
async def stripping_token(
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_nyt_games_client),
) -> None:
    """Test stripping token."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TOKEN: " token "},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_TOKEN: "token"})


@test.cases(
    test.case("invalid_auth", NYTGamesAuthenticationError, "invalid_auth"),
    test.case("cannot_connect", NYTGamesError, "cannot_connect"),
    test.case("unknown", Exception, "unknown"),
)
async def flow_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: AsyncMock = Depends(mock_nyt_games_client),
) -> None:
    """Test flow errors."""
    mock_client.get_user_id.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TOKEN: "token"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    mock_client.get_user_id.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TOKEN: "token"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_nyt_games_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate flow."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TOKEN: "token"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
