"""Tryke fixtures for the Ollama integration."""

from copy import deepcopy
from typing import Any

from tryke import Depends, fixture

from homeassistant.components import ollama
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from . import TEST_AI_TASK_OPTIONS, TEST_OPTIONS, TEST_USER_DATA

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Mock a config entry without API key."""
    data: dict[str, Any] = deepcopy(TEST_USER_DATA)
    entry = MockConfigEntry(
        domain=ollama.DOMAIN,
        data=data,
        version=3,
        minor_version=2,
        subentries_data=[
            {
                "data": dict(TEST_OPTIONS),
                "subentry_type": "conversation",
                "title": "Ollama Conversation",
                "unique_id": None,
            },
            {
                "data": dict(TEST_AI_TASK_OPTIONS),
                "subentry_type": "ai_task_data",
                "title": "Ollama AI Task",
                "unique_id": None,
            },
        ],
    )
    entry.add_to_hass(hass)
    return entry


@fixture
def mock_config_entry_with_token(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Mock a config entry with an API token."""
    data: dict[str, Any] = deepcopy(TEST_USER_DATA)
    data[CONF_API_KEY] = "test_token"
    entry = MockConfigEntry(
        domain=ollama.DOMAIN,
        data=data,
        version=3,
        minor_version=2,
        subentries_data=[
            {
                "data": dict(TEST_OPTIONS),
                "subentry_type": "conversation",
                "title": "Ollama Conversation",
                "unique_id": None,
            },
            {
                "data": dict(TEST_AI_TASK_OPTIONS),
                "subentry_type": "ai_task_data",
                "title": "Ollama AI Task",
                "unique_id": None,
            },
        ],
    )
    entry.add_to_hass(hass)
    return entry
