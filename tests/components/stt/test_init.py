"""Test STT component setup."""

from collections.abc import Iterable
from contextlib import ExitStack
from http import HTTPStatus
from pathlib import Path
from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.stt import (
    DOMAIN,
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechAudioProcessing,
    async_default_engine,
    async_get_provider,
    async_get_speech_to_text_engine,
)
from homeassistant.config_entries import ConfigEntry, ConfigEntryState, ConfigFlow
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.setup import async_setup_component

from .common import (
    TEST_DOMAIN,
    MockSTTProvider,
    MockSTTProviderEntity,
    mock_stt_entity_platform,
    mock_stt_platform,
)

from tests.common import (
    MockConfigEntry,
    MockModule,
    mock_config_flow,
    mock_integration,
    mock_platform,
    mock_restore_cache,
)
from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fixture,
    hass_client as hass_client_fixture,
    hass_ws_client as hass_ws_client_fixture,
    mock_network,
    tmp_path as tmp_path_fixture,
)
from tests.typing import WebSocketGenerator


class STTFlow(ConfigFlow):
    """Test flow."""


@fixture
def config_flow_test_domains() -> Iterable[str]:
    """Test domain fixture."""
    return (TEST_DOMAIN,)


@fixture
def config_flow_setup(
    hass: HomeAssistant = Depends(hass_fixture),
    config_flow_test_domains: Iterable[str] = Depends(config_flow_test_domains),
):
    """Mock config flow for the configured test domains."""
    for domain in config_flow_test_domains:
        mock_platform(hass, f"{domain}.config_flow")

    with ExitStack() as stack:
        for domain in config_flow_test_domains:
            stack.enter_context(mock_config_flow(domain, STTFlow))
        yield


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _config_flow: None = Depends(config_flow_setup),
) -> int:
    """Anchor fixture so tryke fully resolves Depends across the module."""
    return 0


async def mock_setup(
    hass: HomeAssistant,
    tmp_path: Path,
    mock_provider: MockSTTProvider,
) -> None:
    """Set up a test provider."""
    mock_stt_platform(
        hass,
        tmp_path,
        TEST_DOMAIN,
        async_get_engine=AsyncMock(return_value=mock_provider),
    )
    assert await async_setup_component(hass, "stt", {"stt": {"platform": TEST_DOMAIN}})
    await hass.async_block_till_done()


async def mock_config_entry_setup(
    hass: HomeAssistant,
    tmp_path: Path,
    mock_provider_entity: MockSTTProviderEntity,
    test_domain: str = TEST_DOMAIN,
) -> MockConfigEntry:
    """Set up a test provider via config entry."""

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.STT]
        )
        return True

    async def async_unload_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Unload up test config entry."""
        await hass.config_entries.async_forward_entry_unload(config_entry, Platform.STT)
        return True

    mock_integration(
        hass,
        MockModule(
            test_domain,
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

    mock_stt_entity_platform(hass, tmp_path, test_domain, async_setup_entry_platform)

    config_entry = MockConfigEntry(domain=test_domain)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    return config_entry


async def _do_setup(
    setup_kind: str, hass: HomeAssistant, tmp_path: Path
) -> MockSTTProvider | MockSTTProviderEntity:
    """Dispatch for the ``setup`` indirect-parametrize from pytest."""
    if setup_kind == "mock_setup":
        provider = MockSTTProvider()
        await mock_setup(hass, tmp_path, provider)
        return provider
    if setup_kind == "mock_config_entry_setup":
        entity = MockSTTProviderEntity()
        await mock_config_entry_setup(hass, tmp_path, entity)
        return entity
    raise RuntimeError("Invalid setup fixture")


@test.cases(
    test.case("mock_setup", setup_kind="mock_setup"),
    test.case("mock_config_entry_setup", setup_kind="mock_config_entry_setup"),
)
async def get_provider_info(
    setup_kind: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test engine that doesn't exist."""
    setup = await _do_setup(setup_kind, hass, tmp_path)
    client = await hass_client()
    response = await client.get(f"/api/stt/{setup.url_path}")
    expect(response.status).to_equal(HTTPStatus.OK)
    expect(await response.json()).to_equal(
        {
            "languages": ["de", "de-CH", "en"],
            "formats": ["wav", "ogg"],
            "codecs": ["pcm", "opus"],
            "sample_rates": [16000],
            "bit_rates": [16],
            "channels": [1],
        }
    )


@test.cases(
    test.case("mock_setup", setup_kind="mock_setup"),
    test.case("mock_config_entry_setup", setup_kind="mock_config_entry_setup"),
)
async def non_existing_provider(
    setup_kind: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test streaming to engine that doesn't exist."""
    await _do_setup(setup_kind, hass, tmp_path)
    client = await hass_client()

    response = await client.get("/api/stt/not_exist")
    expect(response.status).to_equal(HTTPStatus.NOT_FOUND)

    response = await client.post(
        "/api/stt/not_exist",
        headers={
            "X-Speech-Content": (
                "format=wav; codec=pcm; sample_rate=16000; bit_rate=16; channel=1;"
                " language=en"
            )
        },
    )
    expect(response.status).to_equal(HTTPStatus.NOT_FOUND)


@test.cases(
    test.case("mock_setup", setup_kind="mock_setup"),
    test.case("mock_config_entry_setup", setup_kind="mock_config_entry_setup"),
)
async def stream_audio(
    setup_kind: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test streaming audio and getting response."""
    setup = await _do_setup(setup_kind, hass, tmp_path)
    client = await hass_client()
    response = await client.post(
        f"/api/stt/{setup.url_path}",
        headers={
            "X-Speech-Content": (
                "format=wav; codec=pcm; sample_rate=16000; bit_rate=16; channel=1;"
                " language=en"
            )
        },
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    expect(await response.json()).to_equal(
        {"text": "test_result", "result": "success"}
    )


@test.cases(
    test.case("mock_setup", setup_kind="mock_setup"),
    test.case("mock_config_entry_setup", setup_kind="mock_config_entry_setup"),
)
async def stream_audio_uses_enum_values(
    setup_kind: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test that HTTP API passes enum values to async_process_audio_stream."""
    setup = await _do_setup(setup_kind, hass, tmp_path)
    client = await hass_client()
    response = await client.post(
        f"/api/stt/{setup.url_path}",
        headers={
            "X-Speech-Content": (
                "format=wav; codec=pcm; sample_rate=16000; bit_rate=16; channel=1;"
                " language=en"
            )
        },
    )
    expect(response.status).to_equal(HTTPStatus.OK)

    expect(setup.calls).to_have_length(1)
    metadata, _ = setup.calls[0]

    expect(isinstance(metadata.format, AudioFormats)).to_be(True)
    expect(metadata.format).to_equal(AudioFormats.WAV)
    expect(isinstance(metadata.codec, AudioCodecs)).to_be(True)
    expect(metadata.codec).to_equal(AudioCodecs.PCM)
    expect(isinstance(metadata.bit_rate, AudioBitRates)).to_be(True)
    expect(metadata.bit_rate).to_equal(AudioBitRates.BITRATE_16)
    expect(isinstance(metadata.sample_rate, AudioSampleRates)).to_be(True)
    expect(metadata.sample_rate).to_equal(AudioSampleRates.SAMPLERATE_16000)
    expect(isinstance(metadata.channel, AudioChannels)).to_be(True)
    expect(metadata.channel).to_equal(AudioChannels.CHANNEL_MONO)


@test.cases(
    test.case(
        "mock_setup_missing_header",
        setup_kind="mock_setup",
        header=None,
        status=400,
        error="Missing X-Speech-Content header",
    ),
    test.case(
        "mock_setup_unknown_field",
        setup_kind="mock_setup",
        header=(
            "format=wav; codec=pcm; sample_rate=16000; bit_rate=16; channel=100;"
            " language=en; unknown=1"
        ),
        status=400,
        error="Invalid field: unknown",
    ),
    test.case(
        "mock_setup_invalid_channel",
        setup_kind="mock_setup",
        header=(
            "format=wav; codec=pcm; sample_rate=16000; bit_rate=16; channel=100;"
            " language=en"
        ),
        status=400,
        error="Wrong format of X-Speech-Content: 100 is not a valid AudioChannels",
    ),
    test.case(
        "mock_setup_bad_channel",
        setup_kind="mock_setup",
        header=(
            "format=wav; codec=pcm; sample_rate=16000; bit_rate=16; channel=bad channel;"
            " language=en"
        ),
        status=400,
        error="Wrong format of X-Speech-Content: invalid literal for int() with base 10: 'bad channel'",
    ),
    test.case(
        "mock_setup_missing_language",
        setup_kind="mock_setup",
        header="format=wav; codec=pcm; sample_rate=16000",
        status=400,
        error="Missing language in X-Speech-Content header",
    ),
    test.case(
        "mock_config_entry_setup_missing_header",
        setup_kind="mock_config_entry_setup",
        header=None,
        status=400,
        error="Missing X-Speech-Content header",
    ),
    test.case(
        "mock_config_entry_setup_unknown_field",
        setup_kind="mock_config_entry_setup",
        header=(
            "format=wav; codec=pcm; sample_rate=16000; bit_rate=16; channel=100;"
            " language=en; unknown=1"
        ),
        status=400,
        error="Invalid field: unknown",
    ),
    test.case(
        "mock_config_entry_setup_invalid_channel",
        setup_kind="mock_config_entry_setup",
        header=(
            "format=wav; codec=pcm; sample_rate=16000; bit_rate=16; channel=100;"
            " language=en"
        ),
        status=400,
        error="Wrong format of X-Speech-Content: 100 is not a valid AudioChannels",
    ),
    test.case(
        "mock_config_entry_setup_bad_channel",
        setup_kind="mock_config_entry_setup",
        header=(
            "format=wav; codec=pcm; sample_rate=16000; bit_rate=16; channel=bad channel;"
            " language=en"
        ),
        status=400,
        error="Wrong format of X-Speech-Content: invalid literal for int() with base 10: 'bad channel'",
    ),
    test.case(
        "mock_config_entry_setup_missing_language",
        setup_kind="mock_config_entry_setup",
        header="format=wav; codec=pcm; sample_rate=16000",
        status=400,
        error="Missing language in X-Speech-Content header",
    ),
)
async def metadata_errors(
    setup_kind: str,
    header: str | None,
    status: int,
    error: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test metadata errors."""
    setup = await _do_setup(setup_kind, hass, tmp_path)
    client = await hass_client()
    headers: dict[str, str] = {}
    if header:
        headers["X-Speech-Content"] = header

    response = await client.post(f"/api/stt/{setup.url_path}", headers=headers)
    expect(response.status).to_equal(status)
    expect(await response.text()).to_equal(error)


@test
async def get_provider(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test we can get STT providers."""
    mock_provider = MockSTTProvider()
    await mock_setup(hass, tmp_path, mock_provider)
    expect(async_get_provider(hass, TEST_DOMAIN)).to_be(mock_provider)

    # Test getting the default provider
    expect(async_get_provider(hass)).to_be(mock_provider)


@test
async def config_entry_unload(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test we can unload config entry."""
    mock_provider_entity = MockSTTProviderEntity()
    config_entry = await mock_config_entry_setup(hass, tmp_path, mock_provider_entity)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    await hass.config_entries.async_unload(config_entry.entry_id)
    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def restore_state(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test we restore state in the integration."""
    mock_provider_entity = MockSTTProviderEntity()
    entity_id = f"{DOMAIN}.{TEST_DOMAIN}"
    timestamp = "2023-01-01T23:59:59+00:00"
    mock_restore_cache(hass, (State(entity_id, timestamp),))

    config_entry = await mock_config_entry_setup(hass, tmp_path, mock_provider_entity)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    state = hass.states.get(entity_id)
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(timestamp)


@test.cases(
    test.case("mock_setup", setup_kind="mock_setup", engine_id="test", extra_data={"name": "test"}),
    test.case(
        "mock_config_entry_setup",
        setup_kind="mock_config_entry_setup",
        engine_id="stt.test",
        extra_data={},
    ),
)
async def ws_list_engines(
    setup_kind: str,
    engine_id: str,
    extra_data: dict[str, str],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test listing speech-to-text engines."""
    await _do_setup(setup_kind, hass, tmp_path)
    client = await hass_ws_client()

    await client.send_json_auto_id({"type": "stt/engine/list"})

    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "providers": [
                {"engine_id": engine_id, "supported_languages": ["de", "de-CH", "en"]}
                | extra_data
            ]
        }
    )

    await client.send_json_auto_id({"type": "stt/engine/list", "language": "smurfish"})

    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {"providers": [{"engine_id": engine_id, "supported_languages": []} | extra_data]}
    )

    await client.send_json_auto_id({"type": "stt/engine/list", "language": "en"})

    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "providers": [
                {"engine_id": engine_id, "supported_languages": ["en"]} | extra_data
            ]
        }
    )

    await client.send_json_auto_id({"type": "stt/engine/list", "language": "en-UK"})

    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "providers": [
                {"engine_id": engine_id, "supported_languages": ["en"]} | extra_data
            ]
        }
    )

    await client.send_json_auto_id({"type": "stt/engine/list", "language": "de"})
    msg = await client.receive_json()
    expect(msg["type"]).to_equal("result")
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "providers": [
                {"engine_id": engine_id, "supported_languages": ["de", "de-CH"]}
                | extra_data
            ]
        }
    )

    await client.send_json_auto_id(
        {"type": "stt/engine/list", "language": "de", "country": "ch"}
    )
    msg = await client.receive_json()
    expect(msg["type"]).to_equal("result")
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "providers": [
                {"engine_id": engine_id, "supported_languages": ["de-CH", "de"]}
                | extra_data
            ]
        }
    )


@test
async def default_engine_none(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test async_default_engine."""
    expect(await async_setup_component(hass, "stt", {"stt": {}})).to_be(True)
    await hass.async_block_till_done()

    expect(async_default_engine(hass)).to_be_none()


@test
async def default_engine(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test async_default_engine."""
    mock_provider = MockSTTProvider()
    mock_stt_platform(
        hass,
        tmp_path,
        TEST_DOMAIN,
        async_get_engine=AsyncMock(return_value=mock_provider),
    )
    expect(await async_setup_component(hass, "stt", {"stt": {"platform": TEST_DOMAIN}})).to_be(True)
    await hass.async_block_till_done()

    expect(async_default_engine(hass)).to_equal(TEST_DOMAIN)


@test
async def default_engine_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test async_default_engine."""
    mock_provider_entity = MockSTTProviderEntity()
    await mock_config_entry_setup(hass, tmp_path, mock_provider_entity)

    expect(async_default_engine(hass)).to_equal(f"{DOMAIN}.{TEST_DOMAIN}")


# This test overrides config_flow_test_domains to ("new_test",). Tryke
# fixtures don't support param overrides cleanly, so we replicate the
# config-flow setup inline.
@test
async def default_engine_prefer_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test async_default_engine.

    In this tests there's an entity and a legacy provider.
    The test asserts async_default_engine returns the entity.
    """
    mock_provider = MockSTTProvider()
    mock_provider_entity = MockSTTProviderEntity()
    mock_provider_entity.url_path = "stt.new_test"
    mock_provider_entity._attr_name = "New test"

    # Register the extra "new_test" config-flow domain in addition to the
    # default TEST_DOMAIN already wired by ``config_flow_setup``.
    mock_platform(hass, "new_test.config_flow")
    with mock_config_flow("new_test", STTFlow):
        await mock_setup(hass, tmp_path, mock_provider)
        await mock_config_entry_setup(
            hass, tmp_path, mock_provider_entity, test_domain="new_test"
        )
        await hass.async_block_till_done()

        entity_engine = async_get_speech_to_text_engine(hass, "stt.new_test")
        expect(entity_engine).not_.to_be_none()
        expect(entity_engine.name).to_equal("New test")
        provider_engine = async_get_speech_to_text_engine(hass, "test")
        expect(provider_engine).not_.to_be_none()
        expect(provider_engine.name).to_equal("test")
        expect(async_default_engine(hass)).to_equal("stt.new_test")


@test.cases(
    test.case("cloud_then_new_test", domains=("cloud", "new_test")),
    test.case("new_test_then_cloud", domains=("new_test", "cloud")),
)
async def default_engine_prefer_cloud_entity(
    domains: tuple[str, ...],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test async_default_engine.

    In this tests there's an entity from domain cloud, an entity from domain new_test
    and a legacy provider.
    The test asserts async_default_engine returns the entity from domain cloud.
    """
    mock_provider = MockSTTProvider()
    await mock_setup(hass, tmp_path, mock_provider)

    with ExitStack() as stack:
        for domain in domains:
            mock_platform(hass, f"{domain}.config_flow")
            stack.enter_context(mock_config_flow(domain, STTFlow))

        for domain in domains:
            entity = MockSTTProviderEntity()
            entity.url_path = f"stt.{domain}"
            entity._attr_name = f"{domain} STT entity"
            await mock_config_entry_setup(hass, tmp_path, entity, test_domain=domain)
        await hass.async_block_till_done()

        for domain in domains:
            entity_engine = async_get_speech_to_text_engine(
                hass, f"stt.{domain}_stt_entity"
            )
            expect(entity_engine).not_.to_be_none()
            expect(entity_engine.name).to_equal(f"{domain} STT entity")

        provider_engine = async_get_speech_to_text_engine(hass, "test")
        expect(provider_engine).not_.to_be_none()
        expect(provider_engine.name).to_equal("test")
        expect(async_default_engine(hass)).to_equal("stt.cloud_stt_entity")


@test
async def get_engine_legacy(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test async_get_speech_to_text_engine."""
    mock_provider = MockSTTProvider()
    mock_stt_platform(
        hass,
        tmp_path,
        TEST_DOMAIN,
        async_get_engine=AsyncMock(return_value=mock_provider),
    )
    mock_stt_platform(
        hass,
        tmp_path,
        "cloud",
        async_get_engine=AsyncMock(return_value=mock_provider),
    )
    expect(
        await async_setup_component(
            hass, "stt", {"stt": [{"platform": TEST_DOMAIN}, {"platform": "cloud"}]}
        )
    ).to_be(True)
    await hass.async_block_till_done()

    expect(async_get_speech_to_text_engine(hass, "no_such_provider")).to_be_none()
    expect(async_get_speech_to_text_engine(hass, "test")).to_be(mock_provider)


@test
async def get_engine_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test async_get_speech_to_text_engine."""
    mock_provider_entity = MockSTTProviderEntity()
    await mock_config_entry_setup(hass, tmp_path, mock_provider_entity)

    expect(async_get_speech_to_text_engine(hass, "stt.test")).to_be(mock_provider_entity)


@test
async def audio_processing_default(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test that the default audio_processing property returns correct values."""
    mock_provider = MockSTTProvider()
    await mock_setup(hass, tmp_path, mock_provider)

    engine = async_get_speech_to_text_engine(hass, TEST_DOMAIN)
    expect(engine).not_.to_be_none()

    expect(engine.audio_processing.requires_external_vad).to_be(True)
    expect(engine.audio_processing.prefers_auto_gain_enabled).to_be(True)
    expect(engine.audio_processing.prefers_noise_reduction_enabled).to_be(True)


@test
async def audio_processing_entity_default(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test that the default audio_processing property on entity returns correct values."""
    mock_provider_entity = MockSTTProviderEntity()
    await mock_config_entry_setup(hass, tmp_path, mock_provider_entity)

    engine = async_get_speech_to_text_engine(hass, f"{DOMAIN}.{TEST_DOMAIN}")
    expect(engine).not_.to_be_none()

    expect(engine.audio_processing.requires_external_vad).to_be(True)
    expect(engine.audio_processing.prefers_auto_gain_enabled).to_be(True)
    expect(engine.audio_processing.prefers_noise_reduction_enabled).to_be(True)


@test
async def audio_processing_custom(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test that custom audio_processing values are returned correctly."""
    custom_processing = SpeechAudioProcessing(
        requires_external_vad=False,
        prefers_auto_gain_enabled=False,
        prefers_noise_reduction_enabled=False,
    )
    provider = MockSTTProvider(audio_processing=custom_processing)
    await mock_setup(hass, tmp_path, provider)

    engine = async_get_speech_to_text_engine(hass, TEST_DOMAIN)
    expect(engine).not_.to_be_none()

    expect(engine.audio_processing.requires_external_vad).to_be(False)
    expect(engine.audio_processing.prefers_auto_gain_enabled).to_be(False)
    expect(engine.audio_processing.prefers_noise_reduction_enabled).to_be(False)
