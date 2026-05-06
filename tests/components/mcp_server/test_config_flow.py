"""Test the Model Context Protocol Server config flow."""

from typing import Any
from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.mcp_server.const import DOMAIN
from homeassistant.const import CONF_LLM_HASS_API
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import ensure_homeassistant_loaded, mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _ha_loaded: None = Depends(ensure_homeassistant_loaded),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.cases(
    test.case("empty", params={}),
    test.case("with_assist", params={CONF_LLM_HASS_API: ["assist"]}),
)
async def form(
    params: dict[str, Any],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(not result["errors"]).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        params,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Assist")
    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(result["data"]).to_equal({CONF_LLM_HASS_API: ["assist"]})


@test.cases(
    test.case(
        "empty_llm_api",
        params={CONF_LLM_HASS_API: []},
        errors={CONF_LLM_HASS_API: "llm_api_required"},
    ),
)
async def form_errors(
    params: dict[str, Any],
    errors: dict[str, str],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the errors on invalid user input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(not result["errors"]).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        params,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal(errors)
