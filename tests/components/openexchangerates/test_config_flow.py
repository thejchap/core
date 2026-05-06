"""Test the Open Exchange Rates config flow."""

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

from ._fixtures import (
    currencies,
    mock_config_entry,
    mock_latest_rates_config_flow,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _currencies: AsyncMock = Depends(currencies),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test
async def user_create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _latest: AsyncMock = Depends(mock_latest_rates_config_flow),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
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
    expect(result["data"]).to_equal({"api_key": "test-api-key", "base": "USD"})
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    latest: AsyncMock = Depends(mock_latest_rates_config_flow),
) -> None:
    """Test we handle invalid auth."""
    latest.side_effect = OpenExchangeRatesAuthError()
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    latest: AsyncMock = Depends(mock_latest_rates_config_flow),
) -> None:
    """Test we handle cannot connect error."""
    latest.side_effect = OpenExchangeRatesClientError()
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    latest: AsyncMock = Depends(mock_latest_rates_config_flow),
) -> None:
    """Test we handle unknown error."""
    latest.side_effect = Exception()
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _latest: AsyncMock = Depends(mock_latest_rates_config_flow),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort if the service is already configured."""
    config_entry.add_to_hass(hass)
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    currencies_mock: AsyncMock = Depends(currencies),
) -> None:
    """Test we abort if the service fails to retrieve currencies."""
    currencies_mock.side_effect = OpenExchangeRatesClientError()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def currencies_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    currencies_mock: AsyncMock = Depends(currencies),
) -> None:
    """Test we abort if the service times out retrieving currencies."""

    async def currencies_side_effect():
        await asyncio.sleep(1)
        return {"USD": "United States Dollar", "EUR": "Euro"}

    currencies_mock.side_effect = currencies_side_effect

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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    latest: AsyncMock = Depends(mock_latest_rates_config_flow),
) -> None:
    """Test we abort if the service times out retrieving latest rates."""

    async def latest_rates_side_effect(*args: Any, **kwargs: Any) -> dict[str, float]:
        await asyncio.sleep(1)
        return {"EUR": 1.0}

    latest.side_effect = latest_rates_side_effect

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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    latest: AsyncMock = Depends(mock_latest_rates_config_flow),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we can reauthenticate the config entry."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    latest.side_effect = OpenExchangeRatesAuthError()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "api_key": "invalid-test-api-key",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    latest.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "api_key": "new-test-api-key",
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(len(setup_entry.mock_calls)).to_equal(1)
