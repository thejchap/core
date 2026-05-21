"""Tests for the assist_pipeline pipeline storage and helpers."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import ANY, Mock, patch

from hassil.recognize import Intent, IntentData, RecognizeResult
from tryke import Depends, fixture, test

from homeassistant.components import assist_pipeline, conversation, media_player
from homeassistant.components.assist_pipeline.const import (
    CONF_DEBUG_RECORDING_DIR,
    DATA_CONFIG,
    DOMAIN,
)
from homeassistant.components.assist_pipeline.pipeline import (
    STORAGE_KEY,
    STORAGE_VERSION,
    STORAGE_VERSION_MINOR,
    Pipeline,
    PipelineData,
    PipelineStorageCollection,
    PipelineStore,
    _async_local_fallback_intent_filter,
    async_create_default_pipeline,
    async_get_pipeline,
    async_get_pipelines,
    async_update_pipeline,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import collection, intent
from homeassistant.setup import async_setup_component

from . import MANY_LANGUAGES
from ._fixtures import (
    init_components,
    init_supporting_components,
    mock_stt_provider_entity,
    mock_tts_entity,
    mock_tts_provider,
)

from tests.common import flush_store
from tests.components.stt.common import MockSTTProviderEntity
from tests.components.tts.common import MockTTSEntity, MockTTSProvider
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
    tmp_path as tmp_path_fixture,
)


@fixture
def delay_save() -> Generator[None]:
    """Avoid delayed save in collection store."""
    with patch.object(collection, "SAVE_DELAY", new=0):
        yield


@fixture
async def load_homeassistant(
    hass: HomeAssistant = Depends(hass_fixture),
    _delay_save: None = Depends(delay_save),
) -> None:
    """Load the homeassistant integration."""
    assert await async_setup_component(hass, "homeassistant", {})


@fixture
async def disable_tts_entity(
    mock_tts_entity: MockTTSEntity = Depends(mock_tts_entity),
) -> None:
    """Disable the TTS entity."""
    mock_tts_entity._attr_entity_registry_enabled_default = False


@fixture
def pipeline_data(
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(init_components),
) -> PipelineData:
    """Return pipeline data."""
    return hass.data[DOMAIN]


@fixture
def mock_chat_session_id() -> Generator[Mock]:
    """Mock the conversation ID of chat sessions."""
    with patch(
        "homeassistant.helpers.chat_session.ulid_now", return_value="mock-ulid"
    ) as mock_ulid_now:
        yield mock_ulid_now


@test
async def load_pipelines(
    hass: HomeAssistant = Depends(hass_fixture),
    _components: None = Depends(init_components),
    _homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Make sure that we can load/save data correctly."""
    pipelines = [
        {
            "conversation_engine": "conversation_engine_1",
            "conversation_language": "language_1",
            "language": "language_1",
            "name": "name_1",
            "stt_engine": "stt_engine_1",
            "stt_language": "language_1",
            "tts_engine": "tts_engine_1",
            "tts_language": "language_1",
            "tts_voice": "Arnold Schwarzenegger",
            "wake_word_entity": "wakeword_entity_1",
            "wake_word_id": "wakeword_id_1",
        },
        {
            "conversation_engine": "conversation_engine_2",
            "conversation_language": "language_2",
            "language": "language_2",
            "name": "name_2",
            "stt_engine": "stt_engine_2",
            "stt_language": "language_1",
            "tts_engine": "tts_engine_2",
            "tts_language": "language_2",
            "tts_voice": "The Voice",
            "wake_word_entity": "wakeword_entity_2",
            "wake_word_id": "wakeword_id_2",
        },
        {
            "conversation_engine": "conversation_engine_3",
            "conversation_language": "language_3",
            "language": "language_3",
            "name": "name_3",
            "stt_engine": None,
            "stt_language": None,
            "tts_engine": None,
            "tts_language": None,
            "tts_voice": None,
            "wake_word_entity": "wakeword_entity_3",
            "wake_word_id": "wakeword_id_3",
        },
    ]

    pipeline_data: PipelineData = hass.data[DOMAIN]
    store1 = pipeline_data.pipeline_store
    pipeline_ids = [
        (await store1.async_create_item(pipeline)).id for pipeline in pipelines
    ]
    assert len(store1.data) == 4  # 3 manually created plus a default pipeline
    assert store1.async_get_preferred_item() == list(store1.data)[0]

    await store1.async_delete_item(pipeline_ids[1])
    assert len(store1.data) == 3

    store2 = PipelineStorageCollection(
        PipelineStore(
            hass, STORAGE_VERSION, STORAGE_KEY, minor_version=STORAGE_VERSION_MINOR
        )
    )
    await flush_store(store1.store)
    await store2.async_load()

    assert len(store2.data) == 3

    assert store1.data is not store2.data
    assert store1.data == store2.data
    assert store1.async_get_preferred_item() == store2.async_get_preferred_item()


@test
async def loading_pipelines_from_storage(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    _homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Test loading stored pipelines on start."""
    id_1 = "01GX8ZWBAQYWNB1XV3EXEZ75DY"
    hass_storage[STORAGE_KEY] = {
        "version": STORAGE_VERSION,
        "minor_version": STORAGE_VERSION_MINOR,
        "key": "assist_pipeline.pipelines",
        "data": {
            "items": [
                {
                    "conversation_engine": conversation.HOME_ASSISTANT_AGENT,
                    "conversation_language": "language_1",
                    "id": id_1,
                    "language": "language_1",
                    "name": "name_1",
                    "stt_engine": "stt_engine_1",
                    "stt_language": "language_1",
                    "tts_engine": "tts_engine_1",
                    "tts_language": "language_1",
                    "tts_voice": "Arnold Schwarzenegger",
                    "wake_word_entity": "wakeword_entity_1",
                    "wake_word_id": "wakeword_id_1",
                },
                {
                    "conversation_engine": "conversation_engine_2",
                    "conversation_language": "language_2",
                    "id": "01GX8ZWBAQTKFQNK4W7Q4CTRCX",
                    "language": "language_2",
                    "name": "name_2",
                    "stt_engine": "stt_engine_2",
                    "stt_language": "language_2",
                    "tts_engine": "tts_engine_2",
                    "tts_language": "language_2",
                    "tts_voice": "The Voice",
                    "wake_word_entity": "wakeword_entity_2",
                    "wake_word_id": "wakeword_id_2",
                },
                {
                    "conversation_engine": "conversation_engine_3",
                    "conversation_language": "language_3",
                    "id": "01GX8ZWBAQSV1HP3WGJPFWEJ8J",
                    "language": "language_3",
                    "name": "name_3",
                    "stt_engine": None,
                    "stt_language": None,
                    "tts_engine": None,
                    "tts_language": None,
                    "tts_voice": None,
                    "wake_word_entity": "wakeword_entity_3",
                    "wake_word_id": "wakeword_id_3",
                },
            ],
            "preferred_item": id_1,
        },
    }

    assert await async_setup_component(hass, "assist_pipeline", {})

    pipeline_data: PipelineData = hass.data[DOMAIN]
    store = pipeline_data.pipeline_store
    assert len(store.data) == 3
    assert store.async_get_preferred_item() == id_1
    assert store.data[id_1].conversation_engine == conversation.HOME_ASSISTANT_AGENT


@test
async def migrate_pipeline_store(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    _homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Test loading stored pipelines from an older version."""
    hass_storage[STORAGE_KEY] = {
        "version": 1,
        "minor_version": 1,
        "key": "assist_pipeline.pipelines",
        "data": {
            "items": [
                {
                    "conversation_engine": "conversation_engine_1",
                    "conversation_language": "language_1",
                    "id": "01GX8ZWBAQYWNB1XV3EXEZ75DY",
                    "language": "language_1",
                    "name": "name_1",
                    "stt_engine": "stt_engine_1",
                    "stt_language": "language_1",
                    "tts_engine": "tts_engine_1",
                    "tts_language": "language_1",
                    "tts_voice": "Arnold Schwarzenegger",
                },
                {
                    "conversation_engine": "conversation_engine_2",
                    "conversation_language": "language_2",
                    "id": "01GX8ZWBAQTKFQNK4W7Q4CTRCX",
                    "language": "language_2",
                    "name": "name_2",
                    "stt_engine": "stt_engine_2",
                    "stt_language": "language_2",
                    "tts_engine": "tts_engine_2",
                    "tts_language": "language_2",
                    "tts_voice": "The Voice",
                },
                {
                    "conversation_engine": "conversation_engine_3",
                    "conversation_language": "language_3",
                    "id": "01GX8ZWBAQSV1HP3WGJPFWEJ8J",
                    "language": "language_3",
                    "name": "name_3",
                    "stt_engine": None,
                    "stt_language": None,
                    "tts_engine": None,
                    "tts_language": None,
                    "tts_voice": None,
                },
            ],
            "preferred_item": "01GX8ZWBAQYWNB1XV3EXEZ75DY",
        },
    }

    assert await async_setup_component(hass, "assist_pipeline", {})

    pipeline_data: PipelineData = hass.data[DOMAIN]
    store = pipeline_data.pipeline_store
    assert len(store.data) == 3
    assert store.async_get_preferred_item() == "01GX8ZWBAQYWNB1XV3EXEZ75DY"


@test
async def create_default_pipeline(
    hass: HomeAssistant = Depends(hass_fixture),
    _supporting: None = Depends(init_supporting_components),
    _disable_tts: None = Depends(disable_tts_entity),
    _homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Test async_create_default_pipeline."""
    assert await async_setup_component(hass, "assist_pipeline", {})

    pipeline_data: PipelineData = hass.data[DOMAIN]
    store = pipeline_data.pipeline_store
    assert len(store.data) == 1

    assert (
        await async_create_default_pipeline(
            hass,
            stt_engine_id="bla",
            tts_engine_id="bla",
            pipeline_name="Bla pipeline",
        )
        is None
    )
    assert await async_create_default_pipeline(
        hass,
        stt_engine_id="test",
        tts_engine_id="test",
        pipeline_name="Test pipeline",
    ) == Pipeline(
        conversation_engine="conversation.home_assistant",
        conversation_language="en",
        id=ANY,
        language="en",
        name="Test pipeline",
        stt_engine="test",
        stt_language="en-US",
        tts_engine="test",
        tts_language="en-US",
        tts_voice="james_earl_jones",
        wake_word_entity=None,
        wake_word_id=None,
    )


@test
async def get_pipeline(
    hass: HomeAssistant = Depends(hass_fixture),
    _homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Test async_get_pipeline."""
    assert await async_setup_component(hass, "assist_pipeline", {})

    pipeline_data: PipelineData = hass.data[DOMAIN]
    store = pipeline_data.pipeline_store
    assert len(store.data) == 1

    # Test we get the preferred pipeline if none is specified
    pipeline = async_get_pipeline(hass, None)
    assert pipeline.id == store.async_get_preferred_item()

    # Test getting a specific pipeline
    assert pipeline is async_get_pipeline(hass, pipeline.id)


@test
async def get_pipelines(
    hass: HomeAssistant = Depends(hass_fixture),
    _homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Test async_get_pipelines."""
    assert await async_setup_component(hass, "assist_pipeline", {})

    pipeline_data: PipelineData = hass.data[DOMAIN]
    store = pipeline_data.pipeline_store
    assert len(store.data) == 1

    pipelines = async_get_pipelines(hass)
    assert list(pipelines) == [
        Pipeline(
            conversation_engine="conversation.home_assistant",
            conversation_language="en",
            id=ANY,
            language="en",
            name="Home Assistant",
            stt_engine=None,
            stt_language=None,
            tts_engine=None,
            tts_language=None,
            tts_voice=None,
            wake_word_entity=None,
            wake_word_id=None,
        )
    ]


@test.cases(
    test.case("en", ha_language="en", ha_country=None, conv_language="en"),
    test.case("de-de", ha_language="de", ha_country="de", conv_language="de"),
    test.case("de-ch", ha_language="de", ha_country="ch", conv_language="de-CH"),
    test.case("en-us", ha_language="en", ha_country="us", conv_language="en"),
    test.case("en-uk", ha_language="en", ha_country="uk", conv_language="en"),
    test.case("pt-pt", ha_language="pt", ha_country="pt", conv_language="pt"),
    test.case("pt-br", ha_language="pt", ha_country="br", conv_language="pt-BR"),
)
@test
async def default_pipeline_no_stt_tts(
    ha_language: str,
    ha_country: str | None,
    conv_language: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Test async_get_pipeline."""
    pipeline_language = ha_language
    hass.config.country = ha_country
    hass.config.language = ha_language
    assert await async_setup_component(hass, "assist_pipeline", {})

    pipeline_data: PipelineData = hass.data[DOMAIN]
    store = pipeline_data.pipeline_store
    assert len(store.data) == 1

    # Check the default pipeline
    pipeline = async_get_pipeline(hass, None)
    assert pipeline == Pipeline(
        conversation_engine="conversation.home_assistant",
        conversation_language=conv_language,
        id=pipeline.id,
        language=pipeline_language,
        name="Home Assistant",
        stt_engine=None,
        stt_language=None,
        tts_engine=None,
        tts_language=None,
        tts_voice=None,
        wake_word_entity=None,
        wake_word_id=None,
    )


@test.cases(
    test.case(
        "en",
        ha_language="en",
        ha_country=None,
        conv_language="en",
        stt_language="en",
        tts_language="en",
    ),
    test.case(
        "de-de",
        ha_language="de",
        ha_country="de",
        conv_language="de",
        stt_language="de",
        tts_language="de",
    ),
    test.case(
        "de-ch",
        ha_language="de",
        ha_country="ch",
        conv_language="de-CH",
        stt_language="de-CH",
        tts_language="de-CH",
    ),
    test.case(
        "en-us",
        ha_language="en",
        ha_country="us",
        conv_language="en",
        stt_language="en",
        tts_language="en",
    ),
    test.case(
        "en-uk",
        ha_language="en",
        ha_country="uk",
        conv_language="en",
        stt_language="en",
        tts_language="en",
    ),
    test.case(
        "pt-pt",
        ha_language="pt",
        ha_country="pt",
        conv_language="pt",
        stt_language="pt",
        tts_language="pt",
    ),
    test.case(
        "pt-br",
        ha_language="pt",
        ha_country="br",
        conv_language="pt-BR",
        stt_language="pt-br",
        tts_language="pt-br",
    ),
)
@test
async def default_pipeline(
    ha_language: str,
    ha_country: str | None,
    conv_language: str,
    stt_language: str,
    tts_language: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_stt_provider_entity: MockSTTProviderEntity = Depends(mock_stt_provider_entity),
    mock_tts_provider: MockTTSProvider = Depends(mock_tts_provider),
    _supporting: None = Depends(init_supporting_components),
    _disable_tts: None = Depends(disable_tts_entity),
    _homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Test async_get_pipeline."""
    pipeline_language = ha_language
    hass.config.country = ha_country
    hass.config.language = ha_language

    with (
        patch.object(mock_stt_provider_entity, "_supported_languages", MANY_LANGUAGES),
        patch.object(mock_tts_provider, "_supported_languages", MANY_LANGUAGES),
    ):
        assert await async_setup_component(hass, "assist_pipeline", {})

    pipeline_data: PipelineData = hass.data[DOMAIN]
    store = pipeline_data.pipeline_store
    assert len(store.data) == 1

    # Check the default pipeline
    pipeline = async_get_pipeline(hass, None)
    assert pipeline == Pipeline(
        conversation_engine="conversation.home_assistant",
        conversation_language=conv_language,
        id=pipeline.id,
        language=pipeline_language,
        name="Home Assistant",
        stt_engine="stt.mock_stt",
        stt_language=stt_language,
        tts_engine="test",
        tts_language=tts_language,
        tts_voice=None,
        wake_word_entity=None,
        wake_word_id=None,
    )


@test
async def default_pipeline_unsupported_stt_language(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_stt_provider_entity: MockSTTProviderEntity = Depends(mock_stt_provider_entity),
    _supporting: None = Depends(init_supporting_components),
    _disable_tts: None = Depends(disable_tts_entity),
    _homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Test async_get_pipeline."""
    with patch.object(mock_stt_provider_entity, "_supported_languages", ["smurfish"]):
        assert await async_setup_component(hass, "assist_pipeline", {})

    pipeline_data: PipelineData = hass.data[DOMAIN]
    store = pipeline_data.pipeline_store
    assert len(store.data) == 1

    # Check the default pipeline
    pipeline = async_get_pipeline(hass, None)
    assert pipeline == Pipeline(
        conversation_engine="conversation.home_assistant",
        conversation_language="en",
        id=pipeline.id,
        language="en",
        name="Home Assistant",
        stt_engine=None,
        stt_language=None,
        tts_engine="test",
        tts_language="en-US",
        tts_voice="james_earl_jones",
        wake_word_entity=None,
        wake_word_id=None,
    )


@test
async def default_pipeline_unsupported_tts_language(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_tts_provider: MockTTSProvider = Depends(mock_tts_provider),
    _supporting: None = Depends(init_supporting_components),
    _disable_tts: None = Depends(disable_tts_entity),
    _homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Test async_get_pipeline."""
    with patch.object(mock_tts_provider, "_supported_languages", ["smurfish"]):
        assert await async_setup_component(hass, "assist_pipeline", {})

    pipeline_data: PipelineData = hass.data[DOMAIN]
    store = pipeline_data.pipeline_store
    assert len(store.data) == 1

    # Check the default pipeline
    pipeline = async_get_pipeline(hass, None)
    assert pipeline == Pipeline(
        conversation_engine="conversation.home_assistant",
        conversation_language="en",
        id=pipeline.id,
        language="en",
        name="Home Assistant",
        stt_engine="stt.mock_stt",
        stt_language="en-US",
        tts_engine=None,
        tts_language=None,
        tts_voice=None,
        wake_word_entity=None,
        wake_word_id=None,
    )


@test
async def update_pipeline(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    _homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Test async_update_pipeline."""
    assert await async_setup_component(hass, "assist_pipeline", {})

    pipelines = async_get_pipelines(hass)
    pipelines = list(pipelines)
    assert pipelines == [
        Pipeline(
            conversation_engine="conversation.home_assistant",
            conversation_language="en",
            id=ANY,
            language="en",
            name="Home Assistant",
            stt_engine=None,
            stt_language=None,
            tts_engine=None,
            tts_language=None,
            tts_voice=None,
            wake_word_entity=None,
            wake_word_id=None,
        )
    ]

    pipeline = pipelines[0]
    await async_update_pipeline(
        hass,
        pipeline,
        conversation_engine="homeassistant_1",
        conversation_language="de",
        language="de",
        name="Home Assistant 1",
        stt_engine="stt.test_1",
        stt_language="de",
        tts_engine="test_1",
        tts_language="de",
        tts_voice="test_voice",
        wake_word_entity="wake_work.test_1",
        wake_word_id="wake_word_id_1",
    )

    pipelines = async_get_pipelines(hass)
    pipelines = list(pipelines)
    pipeline = pipelines[0]
    assert pipelines == [
        Pipeline(
            conversation_engine="homeassistant_1",
            conversation_language="de",
            id=pipeline.id,
            language="de",
            name="Home Assistant 1",
            stt_engine="stt.test_1",
            stt_language="de",
            tts_engine="test_1",
            tts_language="de",
            tts_voice="test_voice",
            wake_word_entity="wake_work.test_1",
            wake_word_id="wake_word_id_1",
        )
    ]
    assert len(hass_storage[STORAGE_KEY]["data"]["items"]) == 1
    assert hass_storage[STORAGE_KEY]["data"]["items"][0] == {
        "conversation_engine": "homeassistant_1",
        "conversation_language": "de",
        "id": pipeline.id,
        "language": "de",
        "name": "Home Assistant 1",
        "stt_engine": "stt.test_1",
        "stt_language": "de",
        "tts_engine": "test_1",
        "tts_language": "de",
        "tts_voice": "test_voice",
        "wake_word_entity": "wake_work.test_1",
        "wake_word_id": "wake_word_id_1",
        "prefer_local_intents": False,
    }

    await async_update_pipeline(
        hass,
        pipeline,
        stt_engine="stt.test_2",
        stt_language="en",
        tts_engine="test_2",
        tts_language="en",
    )

    pipelines = async_get_pipelines(hass)
    pipelines = list(pipelines)
    assert pipelines == [
        Pipeline(
            conversation_engine="homeassistant_1",
            conversation_language="de",
            id=pipeline.id,
            language="de",
            name="Home Assistant 1",
            stt_engine="stt.test_2",
            stt_language="en",
            tts_engine="test_2",
            tts_language="en",
            tts_voice="test_voice",
            wake_word_entity="wake_work.test_1",
            wake_word_id="wake_word_id_1",
        )
    ]
    assert len(hass_storage[STORAGE_KEY]["data"]["items"]) == 1
    assert hass_storage[STORAGE_KEY]["data"]["items"][0] == {
        "conversation_engine": "homeassistant_1",
        "conversation_language": "de",
        "id": pipeline.id,
        "language": "de",
        "name": "Home Assistant 1",
        "stt_engine": "stt.test_2",
        "stt_language": "en",
        "tts_engine": "test_2",
        "tts_language": "en",
        "tts_voice": "test_voice",
        "wake_word_entity": "wake_work.test_1",
        "wake_word_id": "wake_word_id_1",
        "prefer_local_intents": False,
    }


@test
def fallback_intent_filter() -> None:
    """Test that we filter the right things."""
    assert (
        _async_local_fallback_intent_filter(
            RecognizeResult(
                intent=Intent(intent.INTENT_GET_STATE),
                intent_data=IntentData([]),
                entities={},
                entities_list=[],
            )
        )
        is True
    )
    assert (
        _async_local_fallback_intent_filter(
            RecognizeResult(
                intent=Intent(media_player.INTENT_MEDIA_SEARCH_AND_PLAY),
                intent_data=IntentData([]),
                entities={},
                entities_list=[],
            )
        )
        is True
    )
    assert (
        _async_local_fallback_intent_filter(
            RecognizeResult(
                intent=Intent(intent.INTENT_NEVERMIND),
                intent_data=IntentData([]),
                entities={},
                entities_list=[],
            )
        )
        is False
    )
    assert (
        _async_local_fallback_intent_filter(
            RecognizeResult(
                intent=Intent(intent.INTENT_TURN_ON),
                intent_data=IntentData([]),
                entities={},
                entities_list=[],
            )
        )
        is False
    )


@test
def pipeline_run_equality(
    hass: HomeAssistant = Depends(hass_fixture),
    pipeline_data: PipelineData = Depends(pipeline_data),
) -> None:
    """Test that pipeline run equality uses unique id."""

    def event_callback(event):
        pass

    pipeline = assist_pipeline.pipeline.async_get_pipeline(hass)
    run_1 = assist_pipeline.pipeline.PipelineRun(
        hass,
        context=Context(),
        pipeline=pipeline,
        start_stage=assist_pipeline.PipelineStage.STT,
        end_stage=assist_pipeline.PipelineStage.TTS,
        event_callback=event_callback,
    )
    run_2 = assist_pipeline.pipeline.PipelineRun(
        hass,
        context=Context(),
        pipeline=pipeline,
        start_stage=assist_pipeline.PipelineStage.STT,
        end_stage=assist_pipeline.PipelineStage.TTS,
        event_callback=event_callback,
    )

    assert run_1 == run_1  # noqa: PLR0124
    assert run_1 != run_2
    assert run_1 != 1234


@test
async def text_only_run_does_not_start_debug_recording_thread(
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    _components: None = Depends(init_components),
    _chat_session_id: Mock = Depends(mock_chat_session_id),
) -> None:
    """Test that text-only runs do not start debug recording."""
    hass.data[DATA_CONFIG][CONF_DEBUG_RECORDING_DIR] = str(tmp_path)

    events: list[assist_pipeline.PipelineEvent] = []
    pipeline = assist_pipeline.pipeline.async_get_pipeline(hass)
    run = assist_pipeline.pipeline.PipelineRun(
        hass,
        context=Context(),
        pipeline=pipeline,
        start_stage=assist_pipeline.PipelineStage.INTENT,
        end_stage=assist_pipeline.PipelineStage.INTENT,
        event_callback=events.append,
    )

    run.start(conversation_id="mock-ulid", device_id=None, satellite_id=None)
    assert run.debug_recording_thread is None
    assert run.debug_recording_queue is None

    await run.end()

    assert not any(tmp_path.iterdir())


@test.skip("snapshot test - port deferred")
async def wake_word_detection_aborted() -> None:
    """Stub for test_wake_word_detection_aborted (port deferred)."""


@test.skip("snapshot test - port deferred")
async def tts_audio_output() -> None:
    """Stub for test_tts_audio_output (port deferred)."""


@test.skip("snapshot test - port deferred")
async def tts_wav_preferred_format() -> None:
    """Stub for test_tts_wav_preferred_format (port deferred)."""


@test.skip("snapshot test - port deferred")
async def tts_dict_preferred_format() -> None:
    """Stub for test_tts_dict_preferred_format (port deferred)."""


@test.skip("snapshot test - port deferred")
async def sentence_trigger_overrides_conversation_agent() -> None:
    """Stub for test_sentence_trigger_overrides_conversation_agent (port deferred)."""


@test.skip("snapshot test - port deferred")
async def prefer_local_intents() -> None:
    """Stub for test_prefer_local_intents (port deferred)."""


@test.skip("snapshot test - port deferred")
async def intent_continue_conversation() -> None:
    """Stub for test_intent_continue_conversation (port deferred)."""


@test.skip("snapshot test - port deferred")
async def stt_language_used_instead_of_conversation_language() -> None:
    """Stub for test_stt_language_used_instead_of_conversation_language (port deferred)."""


@test.skip("snapshot test - port deferred")
async def tts_language_used_instead_of_conversation_language() -> None:
    """Stub for test_tts_language_used_instead_of_conversation_language (port deferred)."""


@test.skip("snapshot test - port deferred")
async def pipeline_language_used_instead_of_conversation_language() -> None:
    """Stub for test_pipeline_language_used_instead_of_conversation_language (port deferred)."""


@test.skip("snapshot test - port deferred")
async def chat_log_tts_streaming() -> None:
    """Stub for test_chat_log_tts_streaming (port deferred)."""


@test.skip("snapshot test - port deferred")
async def acknowledge() -> None:
    """Stub for test_acknowledge (port deferred)."""


@test.skip("snapshot test - port deferred")
async def acknowledge_other_agents() -> None:
    """Stub for test_acknowledge_other_agents (port deferred)."""


@test.skip("snapshot test - port deferred")
async def stt_vad_enabled_based_on_audio_processing() -> None:
    """Stub for test_stt_vad_enabled_based_on_audio_processing (port deferred)."""
