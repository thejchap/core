"""Test wake_word component setup."""

import asyncio
from functools import partial
from pathlib import Path
from typing import Any
from unittest.mock import patch

from freezegun import freeze_time
from tryke import Depends, expect, fixture, test

from homeassistant.components import wake_word
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, State

from ._fixtures import (
    TEST_DOMAIN,
    MockProviderEntity,
    config_flow_fixture as config_flow_fx,
    mock_config_entry_setup,
    mock_provider_entity as mock_provider_entity_fx,
    setup as setup_fx,
)

from tests.common import mock_restore_cache
from tests.hass_fixtures import (
    hass as hass_fx,
    hass_ws_client as hass_ws_client_fx,
    mock_network,
    tmp_path as tmp_path_fx,
)

_SAMPLES_PER_CHUNK = 1024
_BYTES_PER_CHUNK = _SAMPLES_PER_CHUNK * 2  # 16-bit
_MS_PER_CHUNK = (_BYTES_PER_CHUNK // 2) // 16  # 16Khz


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@test
async def config_entry_unload(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    tmp_path: Path = Depends(tmp_path_fx),
    mock_provider_entity: MockProviderEntity = Depends(mock_provider_entity_fx),
    _config_flow: None = Depends(config_flow_fx),
) -> None:
    """Test we can unload config entry."""
    config_entry = await mock_config_entry_setup(hass, tmp_path, mock_provider_entity)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    await hass.config_entries.async_unload(config_entry.entry_id)
    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case("default", wake_word_id=None, expected_ww="test_ww", expected_phrase="Test Phrase"),
    test.case(
        "explicit",
        wake_word_id="test_ww_2",
        expected_ww="test_ww_2",
        expected_phrase="Test Phrase 2",
    ),
)
async def detected_entity(
    wake_word_id: str | None,
    expected_ww: str,
    expected_phrase: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    tmp_path: Path = Depends(tmp_path_fx),
    setup: MockProviderEntity = Depends(setup_fx),
) -> None:
    """Test successful detection through entity."""

    async def three_second_stream():
        timestamp = 0
        while timestamp < 3000:
            yield bytes(_BYTES_PER_CHUNK), timestamp
            timestamp += _MS_PER_CHUNK

    with freeze_time("2023-06-22 10:30:00+00:00"):
        state = setup.state
        expect(state).to_be(None)
        result = await setup.async_process_audio_stream(
            three_second_stream(), wake_word_id
        )
        expect(result).to_equal(
            wake_word.DetectionResult(
                wake_word_id=expected_ww,
                wake_word_phrase=expected_phrase,
                timestamp=2048,
            )
        )

        expect(state != setup.state).to_be(True)
        expect(setup.state).to_equal("2023-06-22T10:30:00+00:00")


@test
async def not_detected_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    setup: MockProviderEntity = Depends(setup_fx),
) -> None:
    """Test unsuccessful detection through entity."""

    async def one_second_stream():
        timestamp = 0
        while timestamp < 1000:
            yield bytes(_BYTES_PER_CHUNK), timestamp
            timestamp += _MS_PER_CHUNK

    state = setup.state
    result = await setup.async_process_audio_stream(one_second_stream(), None)
    expect(result).to_be(None)

    # State should only change when there's a detection
    expect(state).to_equal(setup.state)


@test
async def default_engine_none(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    tmp_path: Path = Depends(tmp_path_fx),
    _config_flow: None = Depends(config_flow_fx),
) -> None:
    """Test async_default_entity."""
    from homeassistant.setup import async_setup_component  # noqa: PLC0415

    expect(
        await async_setup_component(hass, wake_word.DOMAIN, {wake_word.DOMAIN: {}})
    ).to_be(True)
    await hass.async_block_till_done()

    expect(wake_word.async_default_entity(hass)).to_be(None)


@test
async def default_engine_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    tmp_path: Path = Depends(tmp_path_fx),
    mock_provider_entity: MockProviderEntity = Depends(mock_provider_entity_fx),
    _config_flow: None = Depends(config_flow_fx),
) -> None:
    """Test async_default_entity."""
    await mock_config_entry_setup(hass, tmp_path, mock_provider_entity)

    expect(wake_word.async_default_entity(hass)).to_equal(
        f"{wake_word.DOMAIN}.{TEST_DOMAIN}"
    )


@test
async def get_engine_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    tmp_path: Path = Depends(tmp_path_fx),
    mock_provider_entity: MockProviderEntity = Depends(mock_provider_entity_fx),
    _config_flow: None = Depends(config_flow_fx),
) -> None:
    """Test async_get_speech_to_text_engine."""
    await mock_config_entry_setup(hass, tmp_path, mock_provider_entity)

    expect(
        wake_word.async_get_wake_word_detection_entity(
            hass, f"{wake_word.DOMAIN}.test"
        )
    ).to_be(mock_provider_entity)


@test
async def restore_state(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    tmp_path: Path = Depends(tmp_path_fx),
    mock_provider_entity: MockProviderEntity = Depends(mock_provider_entity_fx),
    _config_flow: None = Depends(config_flow_fx),
) -> None:
    """Test we restore state in the integration."""
    entity_id = f"{wake_word.DOMAIN}.{TEST_DOMAIN}"
    timestamp = "2023-01-01T23:59:59+00:00"
    mock_restore_cache(hass, (State(entity_id, timestamp),))

    config_entry = await mock_config_entry_setup(hass, tmp_path, mock_provider_entity)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal(timestamp)


@test
async def entity_attributes(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_provider_entity: MockProviderEntity = Depends(mock_provider_entity_fx),
) -> None:
    """Test that the provider entity attributes match expectations."""
    expect(mock_provider_entity.entity_category).to_be(EntityCategory.DIAGNOSTIC)


@test
async def list_wake_words(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    setup: MockProviderEntity = Depends(setup_fx),
    hass_ws_client: Any = Depends(hass_ws_client_fx),
) -> None:
    """Test that the list_wake_words websocket command works."""
    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 5,
            "type": "wake_word/info",
            "entity_id": setup.entity_id,
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "wake_words": [
                {"id": "test_ww", "name": "Test Wake Word", "phrase": "Test Phrase"},
                {
                    "id": "test_ww_2",
                    "name": "Test Wake Word 2",
                    "phrase": "Test Phrase 2",
                },
            ]
        }
    )


@test
async def list_wake_words_unknown_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    setup: MockProviderEntity = Depends(setup_fx),
    hass_ws_client: Any = Depends(hass_ws_client_fx),
) -> None:
    """Test that the list_wake_words websocket command handles unknown entity."""
    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 5,
            "type": "wake_word/info",
            "entity_id": "wake_word.blah",
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]).to_equal(
        {"code": "not_found", "message": "Entity not found"}
    )


@test
async def list_wake_words_timeout(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    setup: MockProviderEntity = Depends(setup_fx),
    hass_ws_client: Any = Depends(hass_ws_client_fx),
) -> None:
    """Test that the list_wake_words websocket command handles unknown entity."""
    client = await hass_ws_client(hass)

    with (
        patch.object(setup, "get_supported_wake_words", partial(asyncio.sleep, 1)),
        patch("homeassistant.components.wake_word.TIMEOUT_FETCH_WAKE_WORDS", 0),
    ):
        await client.send_json(
            {
                "id": 5,
                "type": "wake_word/info",
                "entity_id": setup.entity_id,
            }
        )

        msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]).to_equal(
        {"code": "timeout", "message": "Timeout fetching wake words"}
    )
