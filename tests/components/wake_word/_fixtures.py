"""Tryke fixtures for wake_word tests."""

from collections.abc import AsyncIterable, Generator
from pathlib import Path

from tryke import Depends, fixture

from homeassistant.components import wake_word
from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .common import mock_wake_word_entity_platform

from tests.common import (
    MockConfigEntry,
    MockModule,
    mock_config_flow,
    mock_integration,
    mock_platform,
)
from tests.hass_fixtures import (
    hass as hass_fixture,
    mock_network,
    tmp_path as tmp_path_fixture,
)

TEST_DOMAIN = "test"


class MockProviderEntity(wake_word.WakeWordDetectionEntity):
    """Mock provider entity."""

    url_path = "wake_word.test"
    _attr_name = "test"

    async def get_supported_wake_words(self) -> list[wake_word.WakeWord]:
        """Return a list of supported wake words."""
        return [
            wake_word.WakeWord(
                id="test_ww", name="Test Wake Word", phrase="Test Phrase"
            ),
            wake_word.WakeWord(
                id="test_ww_2", name="Test Wake Word 2", phrase="Test Phrase 2"
            ),
        ]

    async def _async_process_audio_stream(
        self, stream: AsyncIterable[tuple[bytes, int]], wake_word_id: str | None
    ) -> wake_word.DetectionResult | None:
        """Try to detect wake word(s) in an audio stream with timestamps."""
        if wake_word_id is None:
            wake_word_id = (await self.get_supported_wake_words())[0].id

        wake_word_phrase = wake_word_id
        for ww in await self.get_supported_wake_words():
            if ww.id == wake_word_id:
                wake_word_phrase = ww.phrase or ww.name
                break

        async for _chunk, timestamp in stream:
            if timestamp >= 2000:
                return wake_word.DetectionResult(
                    wake_word_id=wake_word_id,
                    wake_word_phrase=wake_word_phrase,
                    timestamp=timestamp,
                )

        # Not detected
        return None


class WakeWordFlow(ConfigFlow):
    """Test flow."""


@fixture
def mock_provider_entity() -> MockProviderEntity:
    """Test provider entity fixture."""
    return MockProviderEntity()


@fixture
def config_flow_fixture(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[None]:
    """Mock config flow."""
    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")

    with mock_config_flow(TEST_DOMAIN, WakeWordFlow):
        yield


async def mock_config_entry_setup(
    hass: HomeAssistant, tmp_path: Path, mock_provider_entity: MockProviderEntity
) -> MockConfigEntry:
    """Set up a test provider via config entry."""

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.WAKE_WORD]
        )
        return True

    async def async_unload_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Unload up test config entry."""
        await hass.config_entries.async_forward_entry_unload(
            config_entry, Platform.WAKE_WORD
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

    async def async_setup_entry_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up test stt platform via config entry."""
        async_add_entities([mock_provider_entity])

    mock_wake_word_entity_platform(
        hass, tmp_path, TEST_DOMAIN, async_setup_entry_platform
    )

    config_entry = MockConfigEntry(domain=TEST_DOMAIN)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    return config_entry


@fixture
async def setup(
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    _config_flow: None = Depends(config_flow_fixture),
) -> MockProviderEntity:
    """Set up the test environment."""
    provider = MockProviderEntity()
    await mock_config_entry_setup(hass, tmp_path, provider)
    return provider


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0
