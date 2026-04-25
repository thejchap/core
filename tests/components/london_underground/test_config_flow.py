"""Test the London Underground config flow."""

import asyncio
from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.london_underground.const import (
    CONF_LINE,
    DEFAULT_LINES,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_IMPORT, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_config_entry,
    mock_london_underground_client,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def validate_input_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _client: AsyncMock = Depends(mock_london_underground_client),
) -> None:
    """Test successful validation of TfL API."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_LINE: ["Bakerloo", "Central"]},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("London Underground")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal({CONF_LINE: ["Bakerloo", "Central"]})


@test
async def options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test updating options."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_LINE: ["Bakerloo", "Central"],
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_LINE: ["Bakerloo", "Central"],
        }
    )


@test.cases(
    test.case(
        "cannot_connect", side_effect=Exception, expected_error="cannot_connect"
    ),
    test.case(
        "timeout_connect",
        side_effect=asyncio.TimeoutError,
        expected_error="timeout_connect",
    ),
)
async def validate_input_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(mock_london_underground_client),
    *,
    side_effect: type[Exception],
    expected_error: str,
) -> None:
    """Test validation with connection and timeout errors."""
    client.update.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_LINE: ["Bakerloo", "Central"]},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal(expected_error)

    # Confirm recovery after error
    client.update.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("London Underground")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal({CONF_LINE: DEFAULT_LINES})


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_london_underground_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _config: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Try (and fail) setting up a config entry when one already exists."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def yaml_import(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_london_underground_client),
) -> None:
    """Test a YAML sensor is imported and becomes an operational config entry."""
    import_data = {
        "platform": "london_underground",
        "line": ["Central", "Piccadilly", "Victoria", "Bakerloo", "Northern"],
    }
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=import_data
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("London Underground")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(
        {CONF_LINE: ["Central", "Piccadilly", "Victoria", "Bakerloo", "Northern"]}
    )


@test
async def failed_yaml_import_connection(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_london_underground_client),
) -> None:
    """Test a YAML sensor import fails on connection error."""
    client.update.side_effect = asyncio.TimeoutError
    import_data = {
        "platform": "london_underground",
        "line": ["Central", "Piccadilly", "Victoria", "Bakerloo", "Northern"],
    }
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=import_data
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def failed_yaml_import_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_london_underground_client),
    _config: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test a YAML sensor import fails when already configured."""
    import_data = {
        "platform": "london_underground",
        "line": ["Central", "Piccadilly", "Victoria", "Bakerloo", "Northern"],
    }
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=import_data
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")
