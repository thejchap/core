"""Test the Azure Data Explorer config flow."""

from unittest.mock import AsyncMock, MagicMock

from azure.kusto.data.exceptions import KustoAuthenticationError, KustoServiceError
from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant import config_entries, data_entry_flow
from homeassistant.components.azure_data_explorer.const import (
    CONF_ADX_CLUSTER_INGEST_URI,
    CONF_ADX_DATABASE_NAME,
    CONF_ADX_TABLE_NAME,
    CONF_APP_REG_ID,
    CONF_APP_REG_SECRET,
    CONF_AUTHORITY_ID,
    DOMAIN,
)
from homeassistant.core import HomeAssistant

from .const import BASE_CONFIG

from tests.components.azure_data_explorer._fixtures import (
    mock_execute_query,
    mock_managed_streaming,
    mock_queued_ingest,
    mock_setup_entry,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def config_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_managed_streaming: MagicMock = Depends(mock_managed_streaming),
    _mock_queued_ingest: MagicMock = Depends(mock_queued_ingest),
    _mock_execute_query: MagicMock = Depends(mock_execute_query),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=None
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        BASE_CONFIG.copy(),
    )

    expect(result2["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(
        "cluster.region.kusto.windows.net / test-database-name (test-table-name)"
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("cannot_connect", KustoServiceError("test"), "cannot_connect"),
    test.case(
        "invalid_auth", KustoAuthenticationError("test", Exception), "invalid_auth"
    ),
)
async def config_flow_errors(
    test_input: Exception,
    expected: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_managed_streaming: MagicMock = Depends(mock_managed_streaming),
    _mock_queued_ingest: MagicMock = Depends(mock_queued_ingest),
    mock_execute_query: MagicMock = Depends(mock_execute_query),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle connection KustoServiceError."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=None,
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    mock_execute_query.side_effect = test_input
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        BASE_CONFIG.copy(),
    )
    expect(result2["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": expected})

    schema = result2["data_schema"]
    expect(isinstance(schema, vol.Schema)).to_be(True)

    suggested_values = {
        key.schema: key.description.get("suggested_value")
        for key in schema.schema
        if isinstance(key, vol.Marker)
        and key.description
        and "suggested_value" in key.description
    }

    expect(suggested_values[CONF_ADX_CLUSTER_INGEST_URI]).to_equal(
        BASE_CONFIG[CONF_ADX_CLUSTER_INGEST_URI]
    )
    expect(suggested_values[CONF_ADX_DATABASE_NAME]).to_equal(
        BASE_CONFIG[CONF_ADX_DATABASE_NAME]
    )
    expect(suggested_values[CONF_ADX_TABLE_NAME]).to_equal(
        BASE_CONFIG[CONF_ADX_TABLE_NAME]
    )
    expect(suggested_values[CONF_APP_REG_ID]).to_equal(BASE_CONFIG[CONF_APP_REG_ID])
    expect(suggested_values[CONF_APP_REG_SECRET]).to_equal(
        BASE_CONFIG[CONF_APP_REG_SECRET]
    )
    expect(suggested_values[CONF_AUTHORITY_ID]).to_equal(BASE_CONFIG[CONF_AUTHORITY_ID])

    await hass.async_block_till_done()

    expect(result2["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    mock_execute_query.side_effect = None

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        BASE_CONFIG.copy(),
    )

    await hass.async_block_till_done()

    expect(result3["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
