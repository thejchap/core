"""Test the Open Exchange Rates config flow."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, patch

from aioopenexchangerates import (
    OpenExchangeRatesAuthError,
    OpenExchangeRatesClientError,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.openexchangerates.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_currencies,
    mock_latest_rates_config_flow as mock_latest_rates_config_flow_fx,
    mock_setup_entry as mock_setup_entry_fx,
)


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _currencies: AsyncMock = Depends(mock_currencies),
) -> None:
    """Wire mock_network and mock_currencies for every test."""


@test
async def user_create_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_latest_rates_config_flow: AsyncMock = Depends(
        mock_latest_rates_config_flow_fx
    ),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_key": "test-api-key"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("USD")
    expect(result["data"]).to_equal(
        {
            "api_key": "test-api-key",
            "base": "USD",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_latest_rates_config_flow: AsyncMock = Depends(
        mock_latest_rates_config_flow_fx
    ),
) -> None:
    """Test we handle invalid auth."""
    mock_latest_rates_config_flow.side_effect = OpenExchangeRatesAuthError()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_key": "bad-api-key"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_latest_rates_config_flow: AsyncMock = Depends(
        mock_latest_rates_config_flow_fx
    ),
) -> None:
    """Test we handle cannot connect error."""
    mock_latest_rates_config_flow.side_effect = OpenExchangeRatesClientError()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_key": "test-api-key"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unknown_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_latest_rates_config_flow: AsyncMock = Depends(
        mock_latest_rates_config_flow_fx
    ),
) -> None:
    """Test we handle unknown error."""
    mock_latest_rates_config_flow.side_effect = Exception()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_key": "test-api-key"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unknown"})


@test
async def already_configured_service(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_latest_rates_config_flow: AsyncMock = Depends(
        mock_latest_rates_config_flow_fx
    ),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test we abort if the service is already configured."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_key": "test-api-key"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def no_currencies(
    hass: HomeAssistant = Depends(hass_fixture),
    currencies: AsyncMock = Depends(mock_currencies),
) -> None:
    """Test we abort if the service fails to retrieve currencies."""
    currencies.side_effect = OpenExchangeRatesClientError()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def currencies_timeout(
    hass: HomeAssistant = Depends(hass_fixture),
    currencies: AsyncMock = Depends(mock_currencies),
) -> None:
    """Test we abort if the service times out retrieving currencies."""

    async def currencies_side_effect():
        await asyncio.sleep(1)
        return {"USD": "United States Dollar", "EUR": "Euro"}

    currencies.side_effect = currencies_side_effect

    with patch(
        "homeassistant.components.openexchangerates.config_flow.CLIENT_TIMEOUT", 0
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("timeout_connect")


@test
async def latest_rates_timeout(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_latest_rates_config_flow: AsyncMock = Depends(
        mock_latest_rates_config_flow_fx
    ),
) -> None:
    """Test we abort if the service times out retrieving latest rates."""

    async def latest_rates_side_effect(*args: Any, **kwargs: Any) -> dict[str, float]:
        await asyncio.sleep(1)
        return {"EUR": 1.0}

    mock_latest_rates_config_flow.side_effect = latest_rates_side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.openexchangerates.config_flow.CLIENT_TIMEOUT", 0
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"api_key": "test-api-key"},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "timeout_connect"})


@test
async def reauth(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_latest_rates_config_flow: AsyncMock = Depends(
        mock_latest_rates_config_flow_fx
    ),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test we can reauthenticate the config entry."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    mock_latest_rates_config_flow.side_effect = OpenExchangeRatesAuthError()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_key": "invalid-test-api-key"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    mock_latest_rates_config_flow.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_key": "new-test-api-key"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
