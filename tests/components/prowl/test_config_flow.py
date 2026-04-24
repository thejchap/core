"""Test Prowl config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

import prowlpy
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.prowl.const import DOMAIN
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    BAD_API_RESPONSE,
    CONF_INPUT,
    INVALID_API_KEY_ERROR,
    TIMEOUT_ERROR,
    mock_prowlpy as mock_prowlpy_fx,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _prowl: AsyncMock = Depends(mock_prowlpy_fx),
) -> None:
    """Wire mock_network and mock_prowlpy for every test."""


@test
async def flow_user(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_prowlpy: AsyncMock = Depends(mock_prowlpy_fx),
) -> None:
    """Test user initialized flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=CONF_INPUT,
    )

    expect(mock_prowlpy.verify_key.call_count > 0).to_be(True)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(CONF_INPUT[CONF_NAME])
    expect(result["data"]).to_equal({CONF_API_KEY: CONF_INPUT[CONF_API_KEY]})


@test
async def flow_duplicate_api_key(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_prowlpy: AsyncMock = Depends(mock_prowlpy_fx),
) -> None:
    """Test user initialized flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=CONF_INPUT,
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=CONF_INPUT,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)


@test
async def flow_user_bad_key(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_prowlpy: AsyncMock = Depends(mock_prowlpy_fx),
) -> None:
    """Test user submitting a bad API key."""
    mock_prowlpy.verify_key.side_effect = prowlpy.APIError("Invalid API key")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=CONF_INPUT,
    )

    expect(mock_prowlpy.verify_key.call_count > 0).to_be(True)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal(INVALID_API_KEY_ERROR)


@test
async def flow_user_prowl_timeout(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_prowlpy: AsyncMock = Depends(mock_prowlpy_fx),
) -> None:
    """Test Prowl API timeout."""
    mock_prowlpy.verify_key.side_effect = TimeoutError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=CONF_INPUT,
    )

    expect(mock_prowlpy.verify_key.call_count > 0).to_be(True)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal(TIMEOUT_ERROR)


@test
async def flow_api_failure(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_prowlpy: AsyncMock = Depends(mock_prowlpy_fx),
) -> None:
    """Test Prowl API failure."""
    mock_prowlpy.verify_key.side_effect = prowlpy.APIError(BAD_API_RESPONSE)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=CONF_INPUT,
    )

    expect(mock_prowlpy.verify_key.call_count > 0).to_be(True)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal(BAD_API_RESPONSE)
