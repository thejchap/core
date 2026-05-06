"""Test the local_todo config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.local_todo.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    STORAGE_KEY,
    TODO_NAME,
    config_entry as config_entry_fixture,
    mock_setup_entry,
    mock_store,
    setup_integration,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _store: None = Depends(mock_store),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result.get("errors"))).to_be(False)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "todo_list_name": TODO_NAME,
        },
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(TODO_NAME)
    expect(result2["data"]).to_equal(
        {
            "todo_list_name": TODO_NAME,
            "storage_key": STORAGE_KEY,
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def duplicate_todo_list_name(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_integration),
    _entry: MockConfigEntry = Depends(config_entry_fixture),
) -> None:
    """Test two todo-lists cannot be added with the same name."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result.get("errors"))).to_be(False)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            # Pick a name that has the same slugify value as an existing config entry.
            "todo_list_name": "my tasks",
        },
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")
