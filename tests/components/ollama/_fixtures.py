"""Tryke fixtures for Ollama tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from copy import deepcopy
from typing import Any
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.components import ollama
from homeassistant.const import CONF_API_KEY, CONF_LLM_HASS_API
from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

from . import TEST_AI_TASK_OPTIONS, TEST_OPTIONS, TEST_USER_DATA


@fixture
def mock_config_entry_options() -> dict[str, Any]:
    """Fixture for configuration entry options."""
    return TEST_OPTIONS


@fixture
def has_token() -> bool:
    """Fixture to indicate if the config entry has a token."""
    return False


@fixture
def mock_config_entry_data(
    has_token_val: bool = Depends(has_token),
) -> dict[str, Any]:
    """Fixture for configuration entry data."""
    res = deepcopy(TEST_USER_DATA)
    if has_token_val:
        res[CONF_API_KEY] = "test_token"
    return res


@fixture
def mock_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    options: dict[str, Any] = Depends(mock_config_entry_options),
    data: dict[str, Any] = Depends(mock_config_entry_data),
) -> MockConfigEntry:
    """Mock a config entry."""
    entry = MockConfigEntry(
        domain=ollama.DOMAIN,
        data=data,
        version=3,
        minor_version=2,
        subentries_data=[
            {
                "data": {**TEST_OPTIONS, **options},
                "subentry_type": "conversation",
                "title": "Ollama Conversation",
                "unique_id": None,
            },
            {
                "data": TEST_AI_TASK_OPTIONS,
                "subentry_type": "ai_task_data",
                "title": "Ollama AI Task",
                "unique_id": None,
            },
        ],
    )
    entry.add_to_hass(hass)
    return entry


@fixture
def mock_config_entry_with_assist_invalid_api(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> MockConfigEntry:
    """Mock a config entry with assist + an invalid llm api."""
    subentry = next(iter(entry.subentries.values()))
    hass.config_entries.async_update_subentry(
        entry,
        subentry,
        data={
            **subentry.data,
            CONF_LLM_HASS_API: [llm.LLM_API_ASSIST, "invalid_api"],
        },
    )
    return entry


@fixture
async def mock_init_component(
    hass: HomeAssistant = Depends(hass_fixture),
    _entry: MockConfigEntry = Depends(mock_config_entry),
) -> AsyncGenerator[None]:
    """Initialize integration."""
    assert await async_setup_component(hass, "homeassistant", {})
    with patch("ollama.AsyncClient.list"):
        assert await async_setup_component(hass, ollama.DOMAIN, {})
        await hass.async_block_till_done()
        yield


@fixture
async def setup_ha(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up Home Assistant base component."""
    assert await async_setup_component(hass, "homeassistant", {})
