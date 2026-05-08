"""Test the Filter config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.filter.const import (
    CONF_FILTER_NAME,
    CONF_FILTER_PRECISION,
    CONF_FILTER_RADIUS,
    CONF_FILTER_WINDOW_SIZE,
    DEFAULT_FILTER_RADIUS,
    DEFAULT_NAME,
    DEFAULT_PRECISION,
    DEFAULT_WINDOW_SIZE,
    DOMAIN,
    FILTER_NAME_OUTLIER,
)
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry, recorder_mock

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def entry_already_exist(
    _trigger: None = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test abort when entry already exists."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_ENTITY_ID: "sensor.test_monitored",
            CONF_FILTER_NAME: FILTER_NAME_OUTLIER,
        },
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_FILTER_WINDOW_SIZE: DEFAULT_WINDOW_SIZE,
            CONF_FILTER_RADIUS: DEFAULT_FILTER_RADIUS,
            CONF_FILTER_PRECISION: DEFAULT_PRECISION,
        },
    )
    await hass.async_block_till_done()

    # Now try again with the same name and entity_id - should hit duplicate
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_ENTITY_ID: "sensor.test_monitored",
            CONF_FILTER_NAME: FILTER_NAME_OUTLIER,
        },
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_FILTER_WINDOW_SIZE: DEFAULT_WINDOW_SIZE,
            CONF_FILTER_RADIUS: DEFAULT_FILTER_RADIUS,
            CONF_FILTER_PRECISION: DEFAULT_PRECISION,
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.skip("indirect parametrize over (entry_config, options, result_options) not in tryke 0.0.27 — needs test.cases conversion")
async def form() -> None:
    """Stub for test_form (port deferred)."""


@test.skip("requires loaded_entry fixture (depends on values list+recorder pre-setup)")
async def options_flow() -> None:
    """Stub for test_options_flow (port deferred)."""
