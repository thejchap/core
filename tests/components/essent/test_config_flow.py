"""Tests for Essent config flow."""

from unittest.mock import AsyncMock

from essent_dynamic_pricing import (
    EssentConnectionError,
    EssentDataError,
    EssentResponseError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.essent.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_essent_client, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_essent_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test successful config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_be_falsy()

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Essent")
    expect(result["data"]).to_equal({})
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test abort when already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test.cases(
    test.case("conn_err", exception=EssentConnectionError, error="cannot_connect"),
    test.case(
        "resp_err", exception=EssentResponseError("bad"), error="cannot_connect"
    ),
    test.case("data_err", exception=EssentDataError("bad"), error="invalid_data"),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def flow_errors(
    exception: type[Exception] | Exception,
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_essent_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test flow errors."""
    client.async_get_prices.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(error)
