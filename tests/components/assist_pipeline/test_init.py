"""Test Voice Assistant init."""

from __future__ import annotations

import asyncio
from collections.abc import Generator
from pathlib import Path
import tempfile
from unittest.mock import patch
import wave

from tryke import Depends, expect, fixture, test

from homeassistant.components import assist_pipeline, conversation, stt
from homeassistant.components.assist_pipeline.const import (
    BYTES_PER_CHUNK,
    CONF_DEBUG_RECORDING_DIR,
    DOMAIN,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.setup import async_setup_component

from tests.components.assist_pipeline._fixtures import (
    MockWakeWordEntity,
    init_components as init_components_fixture,
    init_supporting_components as init_supporting_components_fixture,
    mock_stt_provider as mock_stt_provider_fixture,
    mock_stt_provider_entity as mock_stt_provider_entity_fixture,
    mock_wake_word_provider_entity as mock_wake_word_provider_entity_fixture,
)
from tests.components.stt.common import MockSTTProvider, MockSTTProviderEntity
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


def _make_10ms_chunk(header: bytes) -> bytes:
    """Return 10ms of zeros with the given header."""
    return header + bytes(BYTES_PER_CHUNK - len(header))


@test.skip("snapshot test - port deferred")
async def pipeline_from_audio_stream_auto() -> None:
    """Stub for test_pipeline_from_audio_stream_auto (port deferred)."""


@test.skip("snapshot test - port deferred")
async def pipeline_from_audio_stream_legacy() -> None:
    """Stub for test_pipeline_from_audio_stream_legacy (port deferred)."""


@test.skip("snapshot test - port deferred")
async def pipeline_from_audio_stream_entity() -> None:
    """Stub for test_pipeline_from_audio_stream_entity (port deferred)."""


@test
async def pipeline_from_audio_stream_no_stt(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    _mock_stt_provider: MockSTTProvider = Depends(mock_stt_provider_fixture),
    _init: None = Depends(init_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test creating a pipeline from an audio stream.

    In this test, the pipeline does not support stt
    """
    client = await hass_ws_client(hass)

    events: list[assist_pipeline.PipelineEvent] = []

    async def audio_data():
        yield _make_10ms_chunk(b"part1")
        yield _make_10ms_chunk(b"part2")
        yield b""

    # Create a pipeline without stt support
    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/create",
            "conversation_engine": conversation.HOME_ASSISTANT_AGENT,
            "conversation_language": "en-US",
            "language": "en",
            "name": "test_name",
            "stt_engine": None,
            "stt_language": None,
            "tts_engine": "test",
            "tts_language": "en-AU",
            "tts_voice": "Arnold Schwarzenegger",
            "wake_word_entity": None,
            "wake_word_id": None,
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    pipeline_id = msg["result"]["id"]

    # Try to use the created pipeline
    await assist_pipeline.async_pipeline_from_audio_stream(
        hass,
        context=Context(),
        event_callback=events.append,
        stt_metadata=stt.SpeechMetadata(
            language="en-UK",
            format=stt.AudioFormats.WAV,
            codec=stt.AudioCodecs.PCM,
            bit_rate=stt.AudioBitRates.BITRATE_16,
            sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
            channel=stt.AudioChannels.CHANNEL_MONO,
        ),
        stt_stream=audio_data(),
        pipeline_id=pipeline_id,
        audio_settings=assist_pipeline.AudioSettings(is_vad_enabled=False),
    )

    expect(len(events)).to_equal(3)
    expect(events[0].type).to_equal(assist_pipeline.PipelineEventType.RUN_START)
    expect(events[1].type).to_equal(assist_pipeline.PipelineEventType.ERROR)
    expect(events[1].data["code"]).to_equal("validation-error")
    expect(events[2].type).to_equal(assist_pipeline.PipelineEventType.RUN_END)


@test
async def pipeline_from_audio_stream_unknown_pipeline(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_stt_provider: MockSTTProvider = Depends(mock_stt_provider_fixture),
    _init: None = Depends(init_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test creating a pipeline from an audio stream.

    In this test, the pipeline does not exist.
    """
    events: list[assist_pipeline.PipelineEvent] = []

    async def audio_data():
        yield _make_10ms_chunk(b"part1")
        yield _make_10ms_chunk(b"part2")
        yield b""

    async def _call() -> None:
        await assist_pipeline.async_pipeline_from_audio_stream(
            hass,
            context=Context(),
            event_callback=events.append,
            stt_metadata=stt.SpeechMetadata(
                language="en-UK",
                format=stt.AudioFormats.WAV,
                codec=stt.AudioCodecs.PCM,
                bit_rate=stt.AudioBitRates.BITRATE_16,
                sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
                channel=stt.AudioChannels.CHANNEL_MONO,
            ),
            stt_stream=audio_data(),
            pipeline_id="blah",
        )

    try:
        await _call()
    except assist_pipeline.PipelineNotFound:
        pass
    else:
        expect(False).to_be(True)

    expect(events).to_equal([])


@test
async def pipeline_from_audio_stream_validation_pipeline_error(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_stt_provider_entity: MockSTTProviderEntity = Depends(
        mock_stt_provider_entity_fixture
    ),
    _init: None = Depends(init_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test validation pipeline errors are emitted as terminal events."""
    events: list[assist_pipeline.PipelineEvent] = []

    await assist_pipeline.async_update_pipeline(
        hass,
        assist_pipeline.async_get_pipeline(hass),
        conversation_engine="conversation.non_existing",
    )

    async def audio_data():
        yield b"audio"

    await assist_pipeline.async_pipeline_from_audio_stream(
        hass,
        context=Context(),
        event_callback=events.append,
        stt_metadata=stt.SpeechMetadata(
            language="",
            format=stt.AudioFormats.WAV,
            codec=stt.AudioCodecs.PCM,
            bit_rate=stt.AudioBitRates.BITRATE_16,
            sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
            channel=stt.AudioChannels.CHANNEL_MONO,
        ),
        stt_stream=audio_data(),
        end_stage=assist_pipeline.PipelineStage.INTENT,
    )

    expect(len(events)).to_equal(3)
    expect(events[0].type).to_equal(assist_pipeline.PipelineEventType.RUN_START)
    expect(events[1].type).to_equal(assist_pipeline.PipelineEventType.ERROR)
    expect(events[1].data).to_equal(
        {
            "code": "intent-not-supported",
            "message": "Intent recognition engine conversation.non_existing is not found",
        }
    )
    expect(events[2].type).to_equal(assist_pipeline.PipelineEventType.RUN_END)


@test.skip("snapshot test - port deferred")
async def pipeline_from_audio_stream_wake_word() -> None:
    """Stub for test_pipeline_from_audio_stream_wake_word (port deferred)."""


@test
async def pipeline_save_audio(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_stt_provider: MockSTTProvider = Depends(mock_stt_provider_fixture),
    _mock_wake_word_provider_entity: MockWakeWordEntity = Depends(
        mock_wake_word_provider_entity_fixture
    ),
    _init_supporting: None = Depends(init_supporting_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test saving audio during a pipeline run."""
    with tempfile.TemporaryDirectory() as temp_dir_str:
        # Enable audio recording to temporary directory
        temp_dir = Path(temp_dir_str)
        expect(
            await async_setup_component(
                hass,
                DOMAIN,
                {DOMAIN: {CONF_DEBUG_RECORDING_DIR: temp_dir_str}},
            )
        ).to_be(True)

        pipeline = assist_pipeline.async_get_pipeline(hass)
        events: list[assist_pipeline.PipelineEvent] = []

        async def audio_data():
            yield _make_10ms_chunk(b"wake word")
            # queued audio
            yield _make_10ms_chunk(b"part1")
            yield _make_10ms_chunk(b"part2")
            yield b""

        await assist_pipeline.async_pipeline_from_audio_stream(
            hass,
            context=Context(),
            event_callback=events.append,
            stt_metadata=stt.SpeechMetadata(
                language="",
                format=stt.AudioFormats.WAV,
                codec=stt.AudioCodecs.PCM,
                bit_rate=stt.AudioBitRates.BITRATE_16,
                sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
                channel=stt.AudioChannels.CHANNEL_MONO,
            ),
            stt_stream=audio_data(),
            pipeline_id=pipeline.id,
            start_stage=assist_pipeline.PipelineStage.WAKE_WORD,
            end_stage=assist_pipeline.PipelineStage.STT,
            audio_settings=assist_pipeline.AudioSettings(is_vad_enabled=False),
        )

        pipeline_dirs = list(temp_dir.iterdir())

        # Only one pipeline run
        # <debug_recording_dir>/<pipeline.name>/<run.id>
        expect(len(pipeline_dirs)).to_equal(1)
        expect(pipeline_dirs[0].is_dir()).to_be(True)
        expect(pipeline_dirs[0].name).to_equal(pipeline.name)

        # Wake and stt files
        run_dirs = list(pipeline_dirs[0].iterdir())
        expect(run_dirs[0].is_dir()).to_be(True)
        run_files = list(run_dirs[0].iterdir())

        expect(len(run_files)).to_equal(2)
        wake_file = run_files[0] if "wake" in run_files[0].name else run_files[1]
        stt_file = run_files[0] if "stt" in run_files[0].name else run_files[1]
        expect(wake_file != stt_file).to_be(True)

        # Verify wake file
        with wave.open(str(wake_file), "rb") as wake_wav:
            wake_data = wake_wav.readframes(wake_wav.getnframes())
            expect(wake_data.startswith(b"wake word")).to_be(True)

        # Verify stt file
        with wave.open(str(stt_file), "rb") as stt_wav:
            stt_data = stt_wav.readframes(stt_wav.getnframes())
            expect(stt_data.startswith(b"queued audio")).to_be(True)
            stt_data = stt_data[len(b"queued audio"):]
            expect(stt_data.startswith(b"part1")).to_be(True)
            stt_data = stt_data[BYTES_PER_CHUNK:]
            expect(stt_data.startswith(b"part2")).to_be(True)


@test
async def pipeline_saved_audio_with_device_id(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_stt_provider: MockSTTProvider = Depends(mock_stt_provider_fixture),
    mock_wake_word_provider_entity: MockWakeWordEntity = Depends(
        mock_wake_word_provider_entity_fixture
    ),
    _init_supporting: None = Depends(init_supporting_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test that saved audio directory uses device id."""
    device_id = "test-device-id"

    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        expect(
            await async_setup_component(
                hass,
                DOMAIN,
                {DOMAIN: {CONF_DEBUG_RECORDING_DIR: temp_dir_str}},
            )
        ).to_be(True)

        def event_callback(event: assist_pipeline.PipelineEvent):
            if event.type == "run-end":
                # Verify that saved audio directory is named after device id
                device_dirs = list(temp_dir.iterdir())
                expect(device_dirs[0].name).to_equal(device_id)

        async def audio_data():
            yield b"not used"

        # Force a timeout during wake word detection
        with patch.object(
            mock_wake_word_provider_entity,
            "async_process_audio_stream",
            side_effect=assist_pipeline.error.WakeWordTimeoutError(
                code="timeout", message="timeout"
            ),
        ):
            await assist_pipeline.async_pipeline_from_audio_stream(
                hass,
                context=Context(),
                event_callback=event_callback,
                stt_metadata=stt.SpeechMetadata(
                    language="",
                    format=stt.AudioFormats.WAV,
                    codec=stt.AudioCodecs.PCM,
                    bit_rate=stt.AudioBitRates.BITRATE_16,
                    sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
                    channel=stt.AudioChannels.CHANNEL_MONO,
                ),
                stt_stream=audio_data(),
                start_stage=assist_pipeline.PipelineStage.WAKE_WORD,
                end_stage=assist_pipeline.PipelineStage.STT,
                device_id=device_id,
            )


@test
async def pipeline_saved_audio_write_error(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_stt_provider: MockSTTProvider = Depends(mock_stt_provider_fixture),
    _mock_wake_word_provider_entity: MockWakeWordEntity = Depends(
        mock_wake_word_provider_entity_fixture
    ),
    _init_supporting: None = Depends(init_supporting_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test that saved audio thread closes WAV file even if there's a write error."""
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        expect(
            await async_setup_component(
                hass,
                DOMAIN,
                {DOMAIN: {CONF_DEBUG_RECORDING_DIR: temp_dir_str}},
            )
        ).to_be(True)

        def event_callback(event: assist_pipeline.PipelineEvent):
            if event.type == "run-end":
                # Verify WAV file exists, but contains no data
                pipeline_dirs = list(temp_dir.iterdir())
                run_dirs = list(pipeline_dirs[0].iterdir())
                wav_path = next(run_dirs[0].iterdir())
                with wave.open(str(wav_path), "rb") as wav_file:
                    expect(wav_file.getnframes()).to_equal(0)

        async def audio_data():
            yield b"not used"

        # Force a timeout during wake word detection
        with patch("wave.Wave_write.writeframes", raises=RuntimeError()):
            await assist_pipeline.async_pipeline_from_audio_stream(
                hass,
                context=Context(),
                event_callback=event_callback,
                stt_metadata=stt.SpeechMetadata(
                    language="",
                    format=stt.AudioFormats.WAV,
                    codec=stt.AudioCodecs.PCM,
                    bit_rate=stt.AudioBitRates.BITRATE_16,
                    sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
                    channel=stt.AudioChannels.CHANNEL_MONO,
                ),
                stt_stream=audio_data(),
                start_stage=assist_pipeline.PipelineStage.WAKE_WORD,
                end_stage=assist_pipeline.PipelineStage.STT,
            )


@test
async def pipeline_saved_audio_empty_queue(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_stt_provider: MockSTTProvider = Depends(mock_stt_provider_fixture),
    _mock_wake_word_provider_entity: MockWakeWordEntity = Depends(
        mock_wake_word_provider_entity_fixture
    ),
    _init_supporting: None = Depends(init_supporting_components_fixture),
    _ulid: None = Depends(mock_chat_session_id),
    _token: None = Depends(mock_tts_token),
) -> None:
    """Test that saved audio thread closes WAV file even if there's an empty queue."""
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        expect(
            await async_setup_component(
                hass,
                DOMAIN,
                {DOMAIN: {CONF_DEBUG_RECORDING_DIR: temp_dir_str}},
            )
        ).to_be(True)

        def event_callback(event: assist_pipeline.PipelineEvent):
            if event.type == "run-end":
                # Verify WAV file exists, but contains no data
                pipeline_dirs = list(temp_dir.iterdir())
                run_dirs = list(pipeline_dirs[0].iterdir())
                wav_path = next(run_dirs[0].iterdir())
                with wave.open(str(wav_path), "rb") as wav_file:
                    expect(wav_file.getnframes()).to_equal(0)

        async def audio_data():
            # Force timeout in _pipeline_debug_recording_thread_proc
            await asyncio.sleep(1)
            yield b"not used"

        # Wrap original function to time out immediately
        _pipeline_debug_recording_thread_proc = (
            assist_pipeline.pipeline._pipeline_debug_recording_thread_proc
        )

        def proc_wrapper(run_recording_dir, queue):
            _pipeline_debug_recording_thread_proc(
                run_recording_dir, queue, message_timeout=0
            )

        with patch(
            "homeassistant.components.assist_pipeline.pipeline._pipeline_debug_recording_thread_proc",
            proc_wrapper,
        ):
            await assist_pipeline.async_pipeline_from_audio_stream(
                hass,
                context=Context(),
                event_callback=event_callback,
                stt_metadata=stt.SpeechMetadata(
                    language="",
                    format=stt.AudioFormats.WAV,
                    codec=stt.AudioCodecs.PCM,
                    bit_rate=stt.AudioBitRates.BITRATE_16,
                    sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
                    channel=stt.AudioChannels.CHANNEL_MONO,
                ),
                stt_stream=audio_data(),
                start_stage=assist_pipeline.PipelineStage.WAKE_WORD,
                end_stage=assist_pipeline.PipelineStage.STT,
            )


@test.skip("snapshot test - port deferred")
async def pipeline_from_audio_stream_with_cloud_auth_fail() -> None:
    """Stub for test_pipeline_from_audio_stream_with_cloud_auth_fail (port deferred)."""
