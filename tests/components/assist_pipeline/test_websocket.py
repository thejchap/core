"""Websocket tests for Voice Assistant integration."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import ANY, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.assist_pipeline.const import DOMAIN
from homeassistant.components.assist_pipeline.pipeline import Pipeline, PipelineData
from homeassistant.core import HomeAssistant

from tests.components.assist_pipeline._fixtures import (
    init_components as init_components_fixture,
)
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fixture,
    mock_network as mock_network_fixture,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network_fixture)) -> int:
    return 0


@fixture
def mock_chat_session_id() -> Generator[None]:
    """Mock the conversation ID of chat sessions."""
    with patch(
        "homeassistant.helpers.chat_session.ulid_now", return_value="mock-ulid"
    ):
        yield


@fixture
def mock_tts_token() -> Generator[None]:
    """Mock the TTS token for URLs."""
    with patch("secrets.token_urlsafe", return_value="mocked-token"):
        yield


@test
async def invalid_stage_order(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    _init: None = Depends(init_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test pipeline run with invalid stage order."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/run",
            "start_stage": "tts",
            "end_stage": "stt",
            "input": {"text": "Lights are on."},
        }
    )

    msg = await client.receive_json()
    expect(msg["success"]).to_be(False)


@test
async def add_pipeline(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    _init: None = Depends(init_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test we can add a pipeline."""
    client = await hass_ws_client(hass)
    pipeline_data: PipelineData = hass.data[DOMAIN]
    pipeline_store = pipeline_data.pipeline_store

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/create",
            "conversation_engine": "test_conversation_engine",
            "conversation_language": "test_language",
            "language": "test_language",
            "name": "test_name",
            "stt_engine": "test_stt_engine",
            "stt_language": "test_language",
            "tts_engine": "test_tts_engine",
            "tts_language": "test_language",
            "tts_voice": "Arnold Schwarzenegger",
            "wake_word_entity": "wakeword_entity_1",
            "wake_word_id": "wakeword_id_1",
            "prefer_local_intents": True,
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "conversation_engine": "test_conversation_engine",
            "conversation_language": "test_language",
            "id": ANY,
            "language": "test_language",
            "name": "test_name",
            "stt_engine": "test_stt_engine",
            "stt_language": "test_language",
            "tts_engine": "test_tts_engine",
            "tts_language": "test_language",
            "tts_voice": "Arnold Schwarzenegger",
            "wake_word_entity": "wakeword_entity_1",
            "wake_word_id": "wakeword_id_1",
            "prefer_local_intents": True,
        }
    )

    expect(len(pipeline_store.data)).to_equal(2)
    pipeline = pipeline_store.data[msg["result"]["id"]]
    expect(pipeline).to_equal(
        Pipeline(
            conversation_engine="test_conversation_engine",
            conversation_language="test_language",
            id=msg["result"]["id"],
            language="test_language",
            name="test_name",
            stt_engine="test_stt_engine",
            stt_language="test_language",
            tts_engine="test_tts_engine",
            tts_language="test_language",
            tts_voice="Arnold Schwarzenegger",
            wake_word_entity="wakeword_entity_1",
            wake_word_id="wakeword_id_1",
            prefer_local_intents=True,
        )
    )

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/create",
            "language": "test_language",
            "name": "test_name",
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(False)


@test
async def add_pipeline_missing_language(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    _init: None = Depends(init_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test we can't add a pipeline without specifying stt or tts language."""
    client = await hass_ws_client(hass)
    pipeline_data: PipelineData = hass.data[DOMAIN]
    pipeline_store = pipeline_data.pipeline_store
    expect(len(pipeline_store.data)).to_equal(1)

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/create",
            "conversation_engine": "test_conversation_engine",
            "conversation_language": "test_language",
            "language": "test_language",
            "name": "test_name",
            "stt_engine": "test_stt_engine",
            "stt_language": None,
            "tts_engine": "test_tts_engine",
            "tts_language": "test_language",
            "tts_voice": "Arnold Schwarzenegger",
            "wake_word_entity": "wakeword_entity_1",
            "wake_word_id": "wakeword_id_1",
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(len(pipeline_store.data)).to_equal(1)

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/create",
            "conversation_engine": "test_conversation_engine",
            "conversation_language": "test_language",
            "language": "test_language",
            "name": "test_name",
            "stt_engine": "test_stt_engine",
            "stt_language": "test_language",
            "tts_engine": "test_tts_engine",
            "tts_language": None,
            "tts_voice": "Arnold Schwarzenegger",
            "wake_word_entity": "wakeword_entity_1",
            "wake_word_id": "wakeword_id_1",
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(len(pipeline_store.data)).to_equal(1)


@test
async def delete_pipeline(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    _init: None = Depends(init_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test we can delete a pipeline."""
    client = await hass_ws_client(hass)
    pipeline_data: PipelineData = hass.data[DOMAIN]
    pipeline_store = pipeline_data.pipeline_store

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/create",
            "conversation_engine": "test_conversation_engine",
            "conversation_language": "test_language",
            "language": "test_language",
            "name": "test_name",
            "stt_engine": "test_stt_engine",
            "stt_language": "test_language",
            "tts_engine": "test_tts_engine",
            "tts_language": "test_language",
            "tts_voice": "Arnold Schwarzenegger",
            "wake_word_entity": "wakeword_entity_1",
            "wake_word_id": "wakeword_id_1",
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    pipeline_id_1 = msg["result"]["id"]

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/create",
            "conversation_engine": "test_conversation_engine",
            "conversation_language": "test_language",
            "language": "test_language",
            "name": "test_name",
            "stt_engine": "test_stt_engine",
            "stt_language": "test_language",
            "tts_engine": "test_tts_engine",
            "tts_language": "test_language",
            "tts_voice": "Arnold Schwarzenegger",
            "wake_word_entity": "wakeword_entity_2",
            "wake_word_id": "wakeword_id_2",
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    pipeline_id_2 = msg["result"]["id"]

    expect(len(pipeline_store.data)).to_equal(3)

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/set_preferred",
            "pipeline_id": pipeline_id_1,
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/delete",
            "pipeline_id": pipeline_id_1,
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(msg["error"]).to_equal(
        {
            "code": "not_allowed",
            "message": f"Item {pipeline_id_1} preferred.",
        }
    )

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/delete",
            "pipeline_id": pipeline_id_2,
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(len(pipeline_store.data)).to_equal(2)

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/delete",
            "pipeline_id": pipeline_id_2,
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(msg["error"]).to_equal(
        {
            "code": "not_found",
            "message": f"Unable to find pipeline_id {pipeline_id_2}",
        }
    )


@test
async def get_pipeline(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    _init: None = Depends(init_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test we can get a pipeline."""
    client = await hass_ws_client(hass)
    pipeline_data: PipelineData = hass.data[DOMAIN]
    pipeline_store = pipeline_data.pipeline_store

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/get",
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "conversation_engine": "conversation.home_assistant",
            "conversation_language": "en",
            "id": ANY,
            "language": "en",
            "name": "Home Assistant",
            "stt_engine": "stt.mock_stt",
            "stt_language": "en-US",
            "tts_engine": "tts.test",
            "tts_language": "en_US",
            "tts_voice": None,
            "wake_word_entity": None,
            "wake_word_id": None,
            "prefer_local_intents": False,
        }
    )

    # Get conversation agent as pipeline
    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/get",
            "pipeline_id": "conversation.home_assistant",
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "conversation_engine": "conversation.home_assistant",
            "conversation_language": "en",
            "id": ANY,
            "language": "en",
            "name": "Home Assistant",
            # It found these defaults
            "stt_engine": "stt.mock_stt",
            "stt_language": "en-US",
            "tts_engine": "tts.test",
            "tts_language": "en_US",
            "tts_voice": None,
            "wake_word_entity": None,
            "wake_word_id": None,
            "prefer_local_intents": False,
        }
    )

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/get",
            "pipeline_id": "no_such_pipeline",
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(msg["error"]).to_equal(
        {
            "code": "not_found",
            "message": "Unable to find pipeline_id no_such_pipeline",
        }
    )

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/create",
            "conversation_engine": "test_conversation_engine",
            "conversation_language": "test_language",
            "language": "test_language",
            "name": "test_name",
            "stt_engine": "test_stt_engine",
            "stt_language": "test_language",
            "tts_engine": "test_tts_engine",
            "tts_language": "test_language",
            "tts_voice": "Arnold Schwarzenegger",
            "wake_word_entity": "wakeword_entity_1",
            "wake_word_id": "wakeword_id_1",
            "prefer_local_intents": False,
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    pipeline_id = msg["result"]["id"]
    expect(len(pipeline_store.data)).to_equal(2)

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/get",
            "pipeline_id": pipeline_id,
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "conversation_engine": "test_conversation_engine",
            "conversation_language": "test_language",
            "id": pipeline_id,
            "language": "test_language",
            "name": "test_name",
            "stt_engine": "test_stt_engine",
            "stt_language": "test_language",
            "tts_engine": "test_tts_engine",
            "tts_language": "test_language",
            "tts_voice": "Arnold Schwarzenegger",
            "wake_word_entity": "wakeword_entity_1",
            "wake_word_id": "wakeword_id_1",
            "prefer_local_intents": False,
        }
    )


@test
async def list_pipelines(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    _init: None = Depends(init_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test we can list pipelines."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "assist_pipeline/pipeline/list"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "pipelines": [
                {
                    "conversation_engine": "conversation.home_assistant",
                    "conversation_language": "en",
                    "id": ANY,
                    "language": "en",
                    "name": "Home Assistant",
                    "stt_engine": "stt.mock_stt",
                    "stt_language": "en-US",
                    "tts_engine": "tts.test",
                    "tts_language": "en_US",
                    "tts_voice": None,
                    "wake_word_entity": None,
                    "wake_word_id": None,
                    "prefer_local_intents": False,
                }
            ],
            "preferred_pipeline": ANY,
        }
    )


@test
async def update_pipeline(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    _init: None = Depends(init_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test we can update a pipeline."""
    client = await hass_ws_client(hass)
    pipeline_data: PipelineData = hass.data[DOMAIN]
    pipeline_store = pipeline_data.pipeline_store

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/update",
            "conversation_engine": "new_conversation_engine",
            "conversation_language": "new_conversation_language",
            "language": "new_language",
            "name": "new_name",
            "pipeline_id": "no_such_pipeline",
            "stt_engine": "new_stt_engine",
            "stt_language": "new_stt_language",
            "tts_engine": "new_tts_engine",
            "tts_language": "new_tts_language",
            "tts_voice": "new_tts_voice",
            "wake_word_entity": "new_wakeword_entity",
            "wake_word_id": "new_wakeword_id",
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(msg["error"]).to_equal(
        {
            "code": "not_found",
            "message": "Unable to find pipeline_id no_such_pipeline",
        }
    )

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/create",
            "conversation_engine": "test_conversation_engine",
            "conversation_language": "test_language",
            "language": "test_language",
            "name": "test_name",
            "stt_engine": "test_stt_engine",
            "stt_language": "test_language",
            "tts_engine": "test_tts_engine",
            "tts_language": "test_language",
            "tts_voice": "Arnold Schwarzenegger",
            "wake_word_entity": "wakeword_entity_1",
            "wake_word_id": "wakeword_id_1",
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    pipeline_id = msg["result"]["id"]
    expect(len(pipeline_store.data)).to_equal(2)

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/update",
            "conversation_engine": "new_conversation_engine",
            "conversation_language": "new_conversation_language",
            "language": "new_language",
            "name": "new_name",
            "pipeline_id": pipeline_id,
            "stt_engine": "new_stt_engine",
            "stt_language": "new_stt_language",
            "tts_engine": "new_tts_engine",
            "tts_language": "new_tts_language",
            "tts_voice": "new_tts_voice",
            "wake_word_entity": "new_wakeword_entity",
            "wake_word_id": "new_wakeword_id",
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "conversation_engine": "new_conversation_engine",
            "conversation_language": "new_conversation_language",
            "id": pipeline_id,
            "language": "new_language",
            "name": "new_name",
            "stt_engine": "new_stt_engine",
            "stt_language": "new_stt_language",
            "tts_engine": "new_tts_engine",
            "tts_language": "new_tts_language",
            "tts_voice": "new_tts_voice",
            "wake_word_entity": "new_wakeword_entity",
            "wake_word_id": "new_wakeword_id",
            "prefer_local_intents": False,
        }
    )

    expect(len(pipeline_store.data)).to_equal(2)
    pipeline = pipeline_store.data[pipeline_id]
    expect(pipeline).to_equal(
        Pipeline(
            conversation_engine="new_conversation_engine",
            conversation_language="new_conversation_language",
            id=pipeline_id,
            language="new_language",
            name="new_name",
            stt_engine="new_stt_engine",
            stt_language="new_stt_language",
            tts_engine="new_tts_engine",
            tts_language="new_tts_language",
            tts_voice="new_tts_voice",
            wake_word_entity="new_wakeword_entity",
            wake_word_id="new_wakeword_id",
        )
    )

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/update",
            "conversation_engine": "new_conversation_engine",
            "conversation_language": "new_conversation_language",
            "language": "new_language",
            "name": "new_name",
            "pipeline_id": pipeline_id,
            "stt_engine": None,
            "stt_language": None,
            "tts_engine": None,
            "tts_language": None,
            "tts_voice": None,
            "wake_word_entity": None,
            "wake_word_id": None,
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "conversation_engine": "new_conversation_engine",
            "conversation_language": "new_conversation_language",
            "id": pipeline_id,
            "language": "new_language",
            "name": "new_name",
            "stt_engine": None,
            "stt_language": None,
            "tts_engine": None,
            "tts_language": None,
            "tts_voice": None,
            "wake_word_entity": None,
            "wake_word_id": None,
            "prefer_local_intents": False,
        }
    )

    pipeline = pipeline_store.data[pipeline_id]
    expect(pipeline).to_equal(
        Pipeline(
            conversation_engine="new_conversation_engine",
            conversation_language="new_conversation_language",
            id=pipeline_id,
            language="new_language",
            name="new_name",
            stt_engine=None,
            stt_language=None,
            tts_engine=None,
            tts_language=None,
            tts_voice=None,
            wake_word_entity=None,
            wake_word_id=None,
        )
    )


@test
async def set_preferred_pipeline(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    _init: None = Depends(init_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test updating the preferred pipeline."""
    client = await hass_ws_client(hass)
    pipeline_data: PipelineData = hass.data[DOMAIN]
    pipeline_store = pipeline_data.pipeline_store

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/create",
            "conversation_engine": "test_conversation_engine",
            "conversation_language": "test_language",
            "language": "test_language",
            "name": "test_name",
            "stt_engine": "test_stt_engine",
            "stt_language": "test_language",
            "tts_engine": "test_tts_engine",
            "tts_language": "test_language",
            "tts_voice": "Arnold Schwarzenegger",
            "wake_word_entity": "wakeword_entity_1",
            "wake_word_id": "wakeword_id_1",
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    pipeline_id_1 = msg["result"]["id"]

    expect(pipeline_store.async_get_preferred_item() != pipeline_id_1).to_be(True)

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/set_preferred",
            "pipeline_id": pipeline_id_1,
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)

    expect(pipeline_store.async_get_preferred_item()).to_equal(pipeline_id_1)


@test
async def set_preferred_pipeline_wrong_id(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    _init: None = Depends(init_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test updating the preferred pipeline with a wrong id."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {"type": "assist_pipeline/pipeline/set_preferred", "pipeline_id": "don_t_exist"}
    )
    msg = await client.receive_json()
    expect(msg["error"]["code"]).to_equal("not_found")


@test
async def pipeline_debug_list_runs_wrong_pipeline(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    _init: None = Depends(init_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test debug listing events from a pipeline."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {"type": "assist_pipeline/pipeline_debug/list", "pipeline_id": "blah"}
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal({"pipeline_runs": []})


@test
async def pipeline_debug_get_run_wrong_pipeline(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    _init: None = Depends(init_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test debug getting a run for a wrong pipeline."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline_debug/get",
            "pipeline_id": "blah",
            "pipeline_run_id": "blah",
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(msg["error"]).to_equal(
        {
            "code": "not_found",
            "message": "pipeline_id blah not found",
        }
    )


@test
async def pipeline_debug_get_run_wrong_pipeline_run(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    _init: None = Depends(init_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test debug getting a wrong run for a pipeline."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/run",
            "start_stage": "intent",
            "end_stage": "intent",
            "input": {"text": "Are the lights on?"},
        }
    )

    # result
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)

    # consume events
    msg = await client.receive_json()
    expect(msg["event"]["type"]).to_equal("run-start")

    msg = await client.receive_json()
    expect(msg["event"]["type"]).to_equal("intent-start")

    msg = await client.receive_json()
    expect(msg["event"]["type"]).to_equal("intent-end")

    msg = await client.receive_json()
    expect(msg["event"]["type"]).to_equal("run-end")

    # Get the id of the pipeline
    await client.send_json_auto_id({"type": "assist_pipeline/pipeline/list"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(len(msg["result"]["pipelines"])).to_equal(1)
    pipeline_id = msg["result"]["pipelines"][0]["id"]

    # get debug data for the wrong run
    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline_debug/get",
            "pipeline_id": pipeline_id,
            "pipeline_run_id": "blah",
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(msg["error"]).to_equal(
        {
            "code": "not_found",
            "message": "pipeline_run_id blah not found",
        }
    )


@test
async def list_pipeline_languages(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    _init: None = Depends(init_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test listing pipeline languages."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "assist_pipeline/language/list"})

    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal({"languages": ["en"]})


@test
async def list_pipeline_languages_with_aliases(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    _init: None = Depends(init_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test listing pipeline languages using aliases."""
    client = await hass_ws_client(hass)

    with (
        patch(
            "homeassistant.components.conversation.async_get_conversation_languages",
            return_value={"he", "nb"},
        ),
        patch(
            "homeassistant.components.stt.async_get_speech_to_text_languages",
            return_value={"he", "no"},
        ),
        patch(
            "homeassistant.components.tts.async_get_text_to_speech_languages",
            return_value={"iw", "nb"},
        ),
    ):
        await client.send_json_auto_id({"type": "assist_pipeline/language/list"})

        msg = await client.receive_json()
        expect(msg["success"]).to_be(True)
        expect(msg["result"]).to_equal({"languages": ["he", "nb"]})


@test.skip("snapshot test - port deferred")
async def text_only_pipeline() -> None:
    """Stub for test_text_only_pipeline (port deferred)."""


@test.skip("snapshot test - port deferred")
async def audio_pipeline() -> None:
    """Stub for test_audio_pipeline (port deferred)."""


@test.skip("snapshot test - port deferred")
async def audio_pipeline_with_wake_word_timeout() -> None:
    """Stub for test_audio_pipeline_with_wake_word_timeout (port deferred)."""


@test.skip("snapshot test - port deferred")
async def audio_pipeline_with_wake_word_no_timeout() -> None:
    """Stub for test_audio_pipeline_with_wake_word_no_timeout (port deferred)."""


@test.skip("snapshot test - port deferred")
async def audio_pipeline_no_wake_word_engine() -> None:
    """Stub for test_audio_pipeline_no_wake_word_engine (port deferred)."""


@test.skip("snapshot test - port deferred")
async def audio_pipeline_no_wake_word_entity() -> None:
    """Stub for test_audio_pipeline_no_wake_word_entity (port deferred)."""


@test.skip("snapshot test - port deferred")
async def intent_timeout() -> None:
    """Stub for test_intent_timeout (port deferred)."""


@test.skip("snapshot test - port deferred")
async def text_pipeline_timeout() -> None:
    """Stub for test_text_pipeline_timeout (port deferred)."""


@test.skip("snapshot test - port deferred")
async def intent_failed() -> None:
    """Stub for test_intent_failed (port deferred)."""


@test.skip("snapshot test - port deferred")
async def audio_pipeline_timeout() -> None:
    """Stub for test_audio_pipeline_timeout (port deferred)."""


@test.skip("snapshot test - port deferred")
async def stt_provider_missing() -> None:
    """Stub for test_stt_provider_missing (port deferred)."""


@test.skip("snapshot test - port deferred")
async def stt_provider_bad_metadata() -> None:
    """Stub for test_stt_provider_bad_metadata (port deferred)."""


@test.skip("snapshot test - port deferred")
async def stt_stream_failed() -> None:
    """Stub for test_stt_stream_failed (port deferred)."""


@test.skip("snapshot test - port deferred")
async def tts_provider_missing() -> None:
    """Stub for test_tts_provider_missing (port deferred)."""


@test.skip("snapshot test - port deferred")
async def tts_provider_bad_options() -> None:
    """Stub for test_tts_provider_bad_options (port deferred)."""


@test.skip("snapshot test - port deferred")
async def audio_pipeline_debug() -> None:
    """Stub for test_audio_pipeline_debug (port deferred)."""


@test.skip("snapshot test - port deferred")
async def audio_pipeline_with_enhancements() -> None:
    """Stub for test_audio_pipeline_with_enhancements (port deferred)."""


@test.skip("snapshot test - port deferred")
async def wake_word_cooldown_same_id() -> None:
    """Stub for test_wake_word_cooldown_same_id (port deferred)."""


@test.skip("snapshot test - port deferred")
async def wake_word_cooldown_different_ids() -> None:
    """Stub for test_wake_word_cooldown_different_ids (port deferred)."""


@test.skip("snapshot test - port deferred")
async def wake_word_cooldown_different_entities() -> None:
    """Stub for test_wake_word_cooldown_different_entities (port deferred)."""


@test.skip("snapshot test - port deferred")
async def device_capture() -> None:
    """Stub for test_device_capture (port deferred)."""


@test.skip("snapshot test - port deferred")
async def device_capture_override() -> None:
    """Stub for test_device_capture_override (port deferred)."""


@test.skip("snapshot test - port deferred")
async def device_capture_queue_full() -> None:
    """Stub for test_device_capture_queue_full (port deferred)."""


@test.skip("snapshot test - port deferred")
async def pipeline_empty_tts_output() -> None:
    """Stub for test_pipeline_empty_tts_output (port deferred)."""


@test.skip("snapshot test - port deferred")
async def pipeline_list_devices() -> None:
    """Stub for test_pipeline_list_devices (port deferred)."""


@test.skip("snapshot test - port deferred")
async def stt_cooldown_same_id() -> None:
    """Stub for test_stt_cooldown_same_id (port deferred)."""


@test.skip("snapshot test - port deferred")
async def stt_cooldown_different_ids() -> None:
    """Stub for test_stt_cooldown_different_ids (port deferred)."""


@test.skip("snapshot test - port deferred")
async def intent_progress_event() -> None:
    """Stub for test_intent_progress_event (port deferred)."""
