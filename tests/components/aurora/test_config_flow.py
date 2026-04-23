"""Test the Aurora config flow."""

from unittest.mock import AsyncMock

from aiohttp import ClientError
from tryke import Depends, expect, fixture, test

from homeassistant.components.aurora.const import CONF_THRESHOLD, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import setup_integration

from tests.common import MockConfigEntry
from tests.components.aurora._fixtures import (
    mock_aurora_client,
    mock_config_entry,
    mock_setup_entry,
)
from tests.hass_fixtures import hass, mock_network

DATA = {
    CONF_LATITUDE: -10,
    CONF_LONGITUDE: 10.2,
}


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_aurora_client: AsyncMock = Depends(mock_aurora_client),
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(result["flow_id"], DATA)
    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("Aurora visibility")
    expect(result["data"]).to_equal(DATA)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("client_error", ClientError, "cannot_connect"),
    test.case("unknown", Exception, "unknown"),
)
async def form_errors(
    side_effect: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_aurora_client: AsyncMock = Depends(mock_aurora_client),
) -> None:
    """Test if invalid response or no connection returned from the API."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    mock_aurora_client.get_forecast_data.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(result["flow_id"], DATA)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": error})

    mock_aurora_client.get_forecast_data.side_effect = None

    result = await hass.config_entries.flow.async_configure(result["flow_id"], DATA)
    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)


@test
async def option_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_aurora_client: AsyncMock = Depends(mock_aurora_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test option flow."""
    await setup_integration(hass, mock_config_entry)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_THRESHOLD: 65},
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["data"][CONF_THRESHOLD]).to_equal(65)
