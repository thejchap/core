"""Test the AEH config flow."""

import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from azure.eventhub.exceptions import EventHubError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.azure_event_hub.const import (
    CONF_MAX_DELAY,
    CONF_SEND_INTERVAL,
    DOMAIN,
    STEP_CONN_STRING,
    STEP_SAS,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .const import (
    BASE_CONFIG_CS,
    BASE_CONFIG_SAS,
    CS_CONFIG,
    CS_CONFIG_FULL,
    IMPORT_CONFIG,
    SAS_CONFIG,
    SAS_CONFIG_FULL,
    UPDATE_OPTIONS,
)

from tests.common import MockConfigEntry
from tests.components.azure_event_hub._fixtures import (
    entry,
    mock_from_connection_string,
    mock_get_eventhub_properties,
    mock_setup_entry,
)
from tests.hass_fixtures import hass, mock_network

_LOGGER = logging.getLogger(__name__)


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case(
        "connection_string", BASE_CONFIG_CS, STEP_CONN_STRING, CS_CONFIG, CS_CONFIG_FULL
    ),
    test.case("sas", BASE_CONFIG_SAS, STEP_SAS, SAS_CONFIG, SAS_CONFIG_FULL),
)
async def form(
    step1_config: dict[str, Any],
    step_id: str,
    step2_config: dict[str, str],
    data_config: dict[str, str],
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_get_eventhub_properties: AsyncMock = Depends(mock_get_eventhub_properties),
    _mock_from_connection_string: MagicMock = Depends(mock_from_connection_string),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=None
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"] is None).to_be(True)
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        step1_config.copy(),
    )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["step_id"]).to_equal(step_id)
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        step2_config.copy(),
    )
    expect(result3["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result3["title"]).to_equal("test-instance")
    expect(result3["data"]).to_equal(data_config)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def import_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_get_eventhub_properties: AsyncMock = Depends(mock_get_eventhub_properties),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    import_config = IMPORT_CONFIG.copy()
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data=IMPORT_CONFIG.copy(),
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("test-instance")
    options = {
        CONF_SEND_INTERVAL: import_config.pop(CONF_SEND_INTERVAL),
        CONF_MAX_DELAY: import_config.pop(CONF_MAX_DELAY),
    }
    expect(result["data"]).to_equal(import_config)
    expect(result["options"]).to_equal(options)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("user", config_entries.SOURCE_USER),
    test.case("import", config_entries.SOURCE_IMPORT),
)
async def single_instance(
    source: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_get_eventhub_properties: AsyncMock = Depends(mock_get_eventhub_properties),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test uniqueness of username."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CS_CONFIG_FULL,
        title="test-instance",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": source},
        data=BASE_CONFIG_CS.copy(),
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test.cases(
    test.case("cannot_connect", EventHubError("test"), "cannot_connect"),
    test.case("unknown", Exception, "unknown"),
)
async def connection_error_sas(
    side_effect: Exception,
    error_message: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_get_eventhub_properties: AsyncMock = Depends(mock_get_eventhub_properties),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle connection errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=BASE_CONFIG_SAS.copy(),
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"] is None).to_be(True)

    mock_get_eventhub_properties.side_effect = side_effect
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        SAS_CONFIG.copy(),
    )
    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": error_message})


@test.cases(
    test.case("cannot_connect", EventHubError("test"), "cannot_connect"),
    test.case("unknown", Exception, "unknown"),
)
async def connection_error_cs(
    side_effect: Exception,
    error_message: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_get_eventhub_properties: AsyncMock = Depends(mock_get_eventhub_properties),
    mock_from_connection_string: MagicMock = Depends(mock_from_connection_string),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle connection errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=BASE_CONFIG_CS.copy(),
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"] is None).to_be(True)
    mock_from_connection_string.return_value.get_eventhub_properties.side_effect = (
        side_effect
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        CS_CONFIG.copy(),
    )
    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": error_message})


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    entry: MockConfigEntry = Depends(entry),
) -> None:
    """Test options flow."""
    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("init")
    expect(bool(result["last_step"])).to_be(True)

    updated = await hass.config_entries.options.async_configure(
        result["flow_id"], UPDATE_OPTIONS
    )
    expect(updated["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(updated["data"]).to_equal(UPDATE_OPTIONS)
    await hass.async_block_till_done()
