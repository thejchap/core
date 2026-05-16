"""Tryke fixtures for Assist Satellite tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
import pathlib
from unittest.mock import Mock, patch

from tryke import Depends, fixture

from homeassistant.components.assist_pipeline import PipelineEvent
from homeassistant.components.assist_satellite import (
    DOMAIN,
    AssistSatelliteAnnouncement,
    AssistSatelliteConfiguration,
    AssistSatelliteEntity,
    AssistSatelliteEntityFeature,
    AssistSatelliteWakeWord,
)
from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.setup import async_setup_component
from homeassistant.util.ulid import ulid_hex

from tests.common import (
    MockConfigEntry,
    MockModule,
    mock_config_flow,
    mock_integration,
    mock_platform,
    setup_test_component_platform,
)
from tests.hass_fixtures import hass as hass_fixture, tmp_path as tmp_path_fixture

TEST_DOMAIN = "test"


class MockAssistSatellite(AssistSatelliteEntity):
    """Mock Assist Satellite Entity."""

    _attr_tts_options = {"test-option": "test-value"}

    def __init__(self, name: str, features: AssistSatelliteEntityFeature) -> None:
        """Initialize the mock entity."""
        self._attr_unique_id = ulid_hex()
        self._attr_device_info = DeviceInfo(
            {
                "name": name,
                "identifiers": {(TEST_DOMAIN, self._attr_unique_id)},
            }
        )
        self._attr_name = name
        self._attr_supported_features = features
        self.events = []
        self.announcements: list[AssistSatelliteAnnouncement] = []
        self.config = AssistSatelliteConfiguration(
            available_wake_words=[
                AssistSatelliteWakeWord(
                    id="1234", wake_word="okay nabu", trained_languages=["en"]
                ),
                AssistSatelliteWakeWord(
                    id="5678",
                    wake_word="hey jarvis",
                    trained_languages=["en"],
                ),
            ],
            active_wake_words=["1234"],
            max_active_wake_words=1,
        )
        self.start_conversations = []

    def on_pipeline_event(self, event: PipelineEvent) -> None:
        """Handle pipeline events."""
        self.events.append(event)

    async def async_announce(self, announcement: AssistSatelliteAnnouncement) -> None:
        """Announce media on a device."""
        self.announcements.append(announcement)

    @callback
    def async_get_configuration(self) -> AssistSatelliteConfiguration:
        """Get the current satellite configuration."""
        return self.config

    async def async_set_configuration(
        self, config: AssistSatelliteConfiguration
    ) -> None:
        """Set the current satellite configuration."""
        self.config = config

    async def async_start_conversation(
        self, start_announcement: AssistSatelliteConfiguration
    ) -> None:
        """Start a conversation from the satellite."""
        self.start_conversations.append(
            (self._conversation_id, self._extra_system_prompt, start_announcement)
        )


@fixture
def mock_tts_cache_dir(
    tmp_path: pathlib.Path = Depends(tmp_path_fixture),
) -> Generator[pathlib.Path]:
    """Mock the TTS cache dir with empty dir."""
    with (
        patch(
            "homeassistant.components.tts._init_tts_cache_dir",
            return_value=str(tmp_path),
        ),
        patch(
            "homeassistant.components.tts._get_cache_files",
            return_value={},
        ),
        patch(
            "homeassistant.components.tts.mutagen.File",
            create=True,
        ),
    ):
        yield tmp_path


@fixture
def entity() -> MockAssistSatellite:
    """Mock Assist Satellite Entity."""
    return MockAssistSatellite(
        "Test Entity",
        AssistSatelliteEntityFeature.ANNOUNCE
        | AssistSatelliteEntityFeature.START_CONVERSATION,
    )


@fixture
def entity2() -> MockAssistSatellite:
    """Mock a second Assist Satellite Entity."""
    return MockAssistSatellite("Test Entity 2", AssistSatelliteEntityFeature.ANNOUNCE)


@fixture
def entity_no_features() -> MockAssistSatellite:
    """Mock a third Assist Satellite Entity."""
    return MockAssistSatellite("Test Entity No features", 0)


@fixture
def config_entry(hass: HomeAssistant = Depends(hass_fixture)) -> ConfigEntry:
    """Mock config entry."""
    entry = MockConfigEntry(domain=TEST_DOMAIN)
    entry.add_to_hass(hass)
    return entry


@fixture
async def init_components(
    hass: HomeAssistant = Depends(hass_fixture),
    _tts_cache: pathlib.Path = Depends(mock_tts_cache_dir),
    config_entry: ConfigEntry = Depends(config_entry),
    entity: MockAssistSatellite = Depends(entity),
    entity2: MockAssistSatellite = Depends(entity2),
    entity_no_features: MockAssistSatellite = Depends(entity_no_features),
) -> AsyncGenerator[ConfigEntry]:
    """Initialize components."""
    assert await async_setup_component(hass, "homeassistant", {})

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.ASSIST_SATELLITE]
        )
        return True

    async def async_unload_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Unload test config entry."""
        await hass.config_entries.async_forward_entry_unload(
            config_entry, Platform.ASSIST_SATELLITE
        )
        return True

    mock_integration(
        hass,
        MockModule(
            TEST_DOMAIN,
            async_setup_entry=async_setup_entry_init,
            async_unload_entry=async_unload_entry_init,
        ),
    )
    setup_test_component_platform(
        hass, DOMAIN, [entity, entity2, entity_no_features], from_config_entry=True
    )
    mock_platform(hass, f"{TEST_DOMAIN}.config_flow", Mock())

    with mock_config_flow(TEST_DOMAIN, ConfigFlow):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    yield config_entry
