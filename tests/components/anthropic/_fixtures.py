"""Tryke fixtures for the Anthropic integration.

NOTE: not all conftest fixtures are re-homed here yet - the full anthropic
config_flow port (including subentry options, snapshot, parametrized
switching) is deferred. The fixtures present below are sufficient for the
small subset of tests we have ported.
"""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

from anthropic.pagination import AsyncPage
from tryke import Depends, fixture

from homeassistant.components.anthropic.const import (
    DEFAULT_AI_TASK_NAME,
    DEFAULT_CONVERSATION_NAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import model_list

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Mock a config entry."""
    entry = MockConfigEntry(
        title="Claude",
        domain="anthropic",
        data={
            "api_key": "bla",
        },
        version=2,
        subentries_data=[
            {
                "data": {},
                "subentry_type": "conversation",
                "title": DEFAULT_CONVERSATION_NAME,
                "unique_id": None,
            },
            {
                "data": {},
                "subentry_type": "ai_task_data",
                "title": DEFAULT_AI_TASK_NAME,
                "unique_id": None,
            },
        ],
    )
    entry.add_to_hass(hass)
    return entry


@fixture
async def setup_ha(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Set up Home Assistant."""
    assert await async_setup_component(hass, "homeassistant", {})


@fixture
async def mock_init_component(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup_ha: None = Depends(setup_ha),
) -> AsyncGenerator[None]:
    """Initialize integration."""
    with patch(
        "anthropic.resources.models.AsyncModels.list",
        new_callable=AsyncMock,
        return_value=AsyncPage(data=model_list),
    ):
        assert await async_setup_component(hass, "anthropic", {})
        await hass.async_block_till_done()
        yield


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setup entry."""
    with patch(
        "homeassistant.components.anthropic.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        yield mock_setup
