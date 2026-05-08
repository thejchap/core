"""Tryke fixtures for the OpenAI Conversation integration."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.components.openai_conversation.const import (
    DEFAULT_AI_TASK_NAME,
    DEFAULT_CONVERSATION_NAME,
    DEFAULT_STT_NAME,
    DEFAULT_TTS_NAME,
    RECOMMENDED_AI_TASK_OPTIONS,
    RECOMMENDED_STT_OPTIONS,
    RECOMMENDED_TTS_OPTIONS,
)
from homeassistant.config_entries import ConfigSubentryData
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Mock a config entry."""
    entry = MockConfigEntry(
        title="OpenAI",
        domain="openai_conversation",
        data={
            "api_key": "bla",
        },
        version=2,
        minor_version=7,
        subentries_data=[
            ConfigSubentryData(
                data={},
                subentry_type="conversation",
                title=DEFAULT_CONVERSATION_NAME,
                unique_id=None,
            ),
            ConfigSubentryData(
                data=RECOMMENDED_AI_TASK_OPTIONS,
                subentry_type="ai_task_data",
                title=DEFAULT_AI_TASK_NAME,
                unique_id=None,
            ),
            ConfigSubentryData(
                data=RECOMMENDED_STT_OPTIONS,
                subentry_type="stt",
                title=DEFAULT_STT_NAME,
                unique_id=None,
            ),
            ConfigSubentryData(
                data=RECOMMENDED_TTS_OPTIONS,
                subentry_type="tts",
                title=DEFAULT_TTS_NAME,
                unique_id=None,
            ),
        ],
    )
    entry.add_to_hass(hass)
    return entry


@fixture
async def mock_init_component(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> Generator[None]:
    """Initialize integration."""
    assert await async_setup_component(hass, "homeassistant", {})
    with patch(
        "openai.resources.models.AsyncModels.list",
    ):
        assert await async_setup_component(hass, "openai_conversation", {})
        await hass.async_block_till_done()
        yield
