"""Define tests for the ReCollect Waste config flow."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from aiorecollect.errors import RecollectError
from tryke import Depends, expect, fixture, test

from homeassistant.components.recollect_waste.const import (
    CONF_PLACE_ID,
    CONF_SERVICE_ID,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_FRIENDLY_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    TEST_PLACE_ID,
    TEST_SERVICE_ID,
    client as client_fx,
    config as config_fx,
    config_entry as config_entry_fx,
    mock_aiorecollect as mock_aiorecollect_fx,
    setup_config_entry as setup_config_entry_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def create_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(client_fx),
    cfg: dict[str, Any] = Depends(config_fx),
    _rec: None = Depends(mock_aiorecollect_fx),
) -> None:
    """Test creating an entry."""
    get_pickup_events_mock = AsyncMock(side_effect=RecollectError)
    get_pickup_events_errors = {"base": "invalid_place_or_service_id"}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch.object(client, "async_get_pickup_events", get_pickup_events_mock):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=cfg
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal(get_pickup_events_errors)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=cfg
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"{TEST_PLACE_ID}, {TEST_SERVICE_ID}")
    expect(result["data"]).to_equal(
        {
            CONF_PLACE_ID: TEST_PLACE_ID,
            CONF_SERVICE_ID: TEST_SERVICE_ID,
        }
    )


@test
async def duplicate_error(
    hass: HomeAssistant = Depends(hass_fixture),
    cfg: dict[str, Any] = Depends(config_fx),
    _setup: None = Depends(setup_config_entry_fx),
) -> None:
    """Test that errors are shown when duplicates are added."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=cfg
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry_fx),
    _setup: None = Depends(setup_config_entry_fx),
) -> None:
    """Test config flow options."""
    result = await hass.config_entries.options.async_init(entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_FRIENDLY_NAME: True}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(entry.options).to_equal({CONF_FRIENDLY_NAME: True})
