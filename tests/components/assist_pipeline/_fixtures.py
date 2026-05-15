"""Tryke fixtures for assist_pipeline tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterable, Generator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components import conversation, stt, tts, wake_word
from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
    MockModule,
    MockPlatform,
    mock_config_flow,
    mock_integration,
    mock_platform,
)
from tests.components.stt.common import MockSTTProvider, MockSTTProviderEntity
from tests.components.tts.common import MockTTSEntity, MockTTSProvider
from tests.hass_fixtures import hass as hass_fixture, tmp_path as tmp_path_fixture

_TRANSCRIPT = "test transcript"


class MockTTSPlatform(MockPlatform):
    """A mock TTS platform."""

    PLATFORM_SCHEMA = tts.PLATFORM_SCHEMA

    def __init__(self, *, async_get_engine, **kwargs: Any) -> None:
        """Initialize the tts platform."""
        super().__init__(**kwargs)
        self.async_get_engine = async_get_engine


class MockSttPlatform(MockPlatform):
    """Provide a fake STT platform."""

    def __init__(self, *, async_get_engine, **kwargs: Any) -> None:
        """Initialize the stt platform."""
        super().__init__(**kwargs)
        self.async_get_engine = async_get_engine


class MockWakeWordEntity(wake_word.WakeWordDetectionEntity):
    """Mock wake word entity."""

    fail_process_audio = False
    url_path = "wake_word.test"
    _attr_name = "test"

    alternate_detections = False
    detected_wake_word_index = 0

    async def get_supported_wake_words(self) -> list[wake_word.WakeWord]:
        """Return a list of supported wake words."""
        return [
            wake_word.WakeWord(id="test_ww", name="Test Wake Word"),
            wake_word.WakeWord(id="test_ww_2", name="Test Wake Word 2"),
        ]

    async def _async_process_audio_stream(
        self, stream: AsyncIterable[tuple[bytes, int]], wake_word_id: str | None
    ) -> wake_word.DetectionResult | None:
        """Try to detect wake word(s) in an audio stream with timestamps."""
        wake_words = await self.get_supported_wake_words()

        if self.alternate_detections:
            detected_id = wake_words[self.detected_wake_word_index].id
            detected_name = wake_words[self.detected_wake_word_index].name
            self.detected_wake_word_index = (self.detected_wake_word_index + 1) % len(
                wake_words
            )
        else:
            detected_id = wake_words[0].id
            detected_name = wake_words[0].name

        async for chunk, timestamp in stream:
            if chunk.startswith(b"wake word"):
                return wake_word.DetectionResult(
                    wake_word_id=detected_id,
                    wake_word_phrase=detected_name,
                    timestamp=timestamp,
                    queued_audio=[(b"queued audio", 0)],
                )

        return None


class MockWakeWordEntity2(wake_word.WakeWordDetectionEntity):
    """Second mock wake word entity to test cooldown."""

    fail_process_audio = False
    url_path = "wake_word.test2"
    _attr_name = "test2"

    async def get_supported_wake_words(self) -> list[wake_word.WakeWord]:
        """Return a list of supported wake words."""
        return [wake_word.WakeWord(id="test_ww", name="Test Wake Word")]

    async def _async_process_audio_stream(
        self, stream: AsyncIterable[tuple[bytes, int]], wake_word_id: str | None
    ) -> wake_word.DetectionResult | None:
        """Try to detect wake word(s) in an audio stream with timestamps."""
        wake_words = await self.get_supported_wake_words()

        async for chunk, timestamp in stream:
            if chunk.startswith(b"wake word"):
                return wake_word.DetectionResult(
                    wake_word_id=wake_words[0].id,
                    wake_word_phrase=wake_words[0].name,
                    timestamp=timestamp,
                    queued_audio=[(b"queued audio", 0)],
                )

        return None


class MockFlow(ConfigFlow):
    """Test flow."""


@fixture
async def mock_tts_provider() -> MockTTSProvider:
    """Mock TTS provider."""
    provider = MockTTSProvider("en")
    provider._supported_languages = ["en-US"]
    return provider


@fixture
def mock_tts_entity() -> MockTTSEntity:
    """Test TTS entity."""
    entity = MockTTSEntity("en")
    entity._attr_unique_id = "test_tts"
    entity._attr_supported_languages = ["en-US"]
    return entity


@fixture
async def mock_stt_provider() -> MockSTTProvider:
    """Mock STT provider."""
    return MockSTTProvider(supported_languages=["en-US"], text=_TRANSCRIPT)


@fixture
def mock_stt_provider_entity() -> MockSTTProviderEntity:
    """Test provider entity fixture."""
    entity = MockSTTProviderEntity(supported_languages=["en-US"], text=_TRANSCRIPT)
    entity._attr_name = "Mock STT"
    return entity


@fixture
async def mock_wake_word_provider_entity() -> MockWakeWordEntity:
    """Mock wake word provider."""
    return MockWakeWordEntity()


@fixture
async def mock_wake_word_provider_entity2() -> MockWakeWordEntity2:
    """Mock wake word provider."""
    return MockWakeWordEntity2()


@fixture
def config_flow_fixture(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[None]:
    """Mock config flow."""
    mock_platform(hass, "test.config_flow")
    with mock_config_flow("test", MockFlow):
        yield


@fixture
def mock_tts_cache_dir_autouse(
    tmp_path: Path = Depends(tmp_path_fixture),
) -> Generator[None]:
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
        yield


@fixture
async def init_supporting_components(
    hass: HomeAssistant = Depends(hass_fixture),
    _cache: None = Depends(mock_tts_cache_dir_autouse),
    mock_stt_provider: MockSTTProvider = Depends(mock_stt_provider),
    mock_stt_provider_entity: MockSTTProviderEntity = Depends(mock_stt_provider_entity),
    mock_tts_provider: MockTTSProvider = Depends(mock_tts_provider),
    mock_tts_entity: MockTTSEntity = Depends(mock_tts_entity),
    mock_wake_word_provider_entity: MockWakeWordEntity = Depends(
        mock_wake_word_provider_entity
    ),
    mock_wake_word_provider_entity2: MockWakeWordEntity2 = Depends(
        mock_wake_word_provider_entity2
    ),
    _config_flow: None = Depends(config_flow_fixture),
) -> None:
    """Initialize relevant components with empty configs."""

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        await hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.STT, Platform.TTS, Platform.WAKE_WORD]
        )
        return True

    async def async_unload_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        await hass.config_entries.async_unload_platforms(
            config_entry, [Platform.STT, Platform.WAKE_WORD]
        )
        return True

    async def async_setup_entry_stt_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        async_add_entities([mock_stt_provider_entity])

    async def async_setup_entry_tts_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        async_add_entities([mock_tts_entity])

    async def async_setup_entry_wake_word_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        async_add_entities(
            [mock_wake_word_provider_entity, mock_wake_word_provider_entity2]
        )

    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=async_setup_entry_init,
            async_unload_entry=async_unload_entry_init,
        ),
    )
    mock_platform(
        hass,
        "test.tts",
        MockTTSPlatform(
            async_get_engine=AsyncMock(return_value=mock_tts_provider),
            async_setup_entry=async_setup_entry_tts_platform,
        ),
    )
    mock_platform(
        hass,
        "test.stt",
        MockSttPlatform(
            async_get_engine=AsyncMock(return_value=mock_stt_provider),
            async_setup_entry=async_setup_entry_stt_platform,
        ),
    )
    mock_platform(
        hass,
        "test.wake_word",
        MockPlatform(
            async_setup_entry=async_setup_entry_wake_word_platform,
        ),
    )
    mock_platform(hass, "test.config_flow")

    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, tts.DOMAIN, {"tts": {"platform": "test"}})
    assert await async_setup_component(hass, stt.DOMAIN, {"stt": {"platform": "test"}})
    assert await async_setup_component(hass, "media_source", {})
    assert await async_setup_component(hass, "conversation", {"conversation": {}})

    # Disable fuzzy matching by default for tests
    agent = conversation.async_get_agent(hass)
    agent.fuzzy_matching = False

    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


@fixture
async def init_components(
    hass: HomeAssistant = Depends(hass_fixture),
    _supporting: None = Depends(init_supporting_components),
) -> None:
    """Initialize assist_pipeline with empty configs."""
    assert await async_setup_component(hass, "assist_pipeline", {})
