"""Test Prowl config flow."""

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
    mock_prowlpy,
)

from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor(
    _prowl: AsyncMock = Depends(mock_prowlpy),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def flow_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    prowl: AsyncMock = Depends(mock_prowlpy),
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

    expect(prowl.verify_key.call_count > 0).to_be(True)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(CONF_INPUT[CONF_NAME])
    expect(result["data"]).to_equal({CONF_API_KEY: CONF_INPUT[CONF_API_KEY]})


@test
async def flow_duplicate_api_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    prowl: AsyncMock = Depends(mock_prowlpy),
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    prowl: AsyncMock = Depends(mock_prowlpy),
) -> None:
    """Test user submitting a bad API key."""
    prowl.verify_key.side_effect = prowlpy.APIError("Invalid API key")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=CONF_INPUT,
    )

    expect(prowl.verify_key.call_count > 0).to_be(True)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal(INVALID_API_KEY_ERROR)


@test
async def flow_user_prowl_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    prowl: AsyncMock = Depends(mock_prowlpy),
) -> None:
    """Test Prowl API timeout."""
    prowl.verify_key.side_effect = TimeoutError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=CONF_INPUT,
    )

    expect(prowl.verify_key.call_count > 0).to_be(True)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal(TIMEOUT_ERROR)


@test
async def flow_api_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    prowl: AsyncMock = Depends(mock_prowlpy),
) -> None:
    """Test Prowl API failure."""
    prowl.verify_key.side_effect = prowlpy.APIError(BAD_API_RESPONSE)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=CONF_INPUT,
    )

    expect(prowl.verify_key.call_count > 0).to_be(True)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal(BAD_API_RESPONSE)
