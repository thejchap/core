"""The tests for the Yandex SpeechKit speech platform."""

from collections.abc import Generator
from http import HTTPStatus
from pathlib import Path
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import tts
from homeassistant.components.media_player import (
    ATTR_MEDIA_CONTENT_ID,
    DOMAIN as MP_DOMAIN,
    SERVICE_PLAY_MEDIA,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import assert_setup_component, async_mock_service
from tests.components.tts.common import retrieve_media
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    hass_client as hass_client_fixture,
    mock_network,
    tmp_path as tmp_path_fixture,
)
from tests.test_util.aiohttp import AiohttpClientMocker
from tests.typing import ClientSessionGenerator

URL = "https://tts.voicetech.yandex.net/generate?"


@fixture
def mock_tts_cache_dir(
    tmp_path: Path = Depends(tmp_path_fixture),
) -> Generator[None]:
    """Mock the TTS cache dir."""
    with (
        patch(
            "homeassistant.components.tts._init_tts_cache_dir",
            return_value=str(tmp_path),
        ),
        patch(
            "homeassistant.components.tts._get_cache_files",
            return_value={},
        ),
    ):
        yield


@fixture
def tts_mutagen_mock() -> Generator[None]:
    """Mock writing tags."""
    with patch(
        "homeassistant.components.tts.SpeechManager.write_tags",
        side_effect=lambda *args: args[1],
    ):
        yield


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _cache: None = Depends(mock_tts_cache_dir),
    _mutagen: None = Depends(tts_mutagen_mock),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def setup_component(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup component."""
    config = {tts.DOMAIN: {"platform": "yandextts", "api_key": "1234567xx"}}

    with assert_setup_component(1, tts.DOMAIN):
        await async_setup_component(hass, tts.DOMAIN, config)
        await hass.async_block_till_done()


@test
async def setup_component_without_api_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup component without api key."""
    config = {tts.DOMAIN: {"platform": "yandextts"}}

    with assert_setup_component(0, tts.DOMAIN):
        await async_setup_component(hass, tts.DOMAIN, config)
        await hass.async_block_till_done()


@test
async def service_say(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test service call say."""
    calls = async_mock_service(hass, MP_DOMAIN, SERVICE_PLAY_MEDIA)

    url_param = {
        "text": "HomeAssistant",
        "lang": "en-US",
        "key": "1234567xx",
        "speaker": "zahar",
        "format": "mp3",
        "emotion": "neutral",
        "speed": 1,
    }
    aioclient_mock.get(URL, status=HTTPStatus.OK, content=b"test", params=url_param)

    config = {tts.DOMAIN: {"platform": "yandextts", "api_key": "1234567xx"}}

    with assert_setup_component(1, tts.DOMAIN):
        await async_setup_component(hass, tts.DOMAIN, config)
        await hass.async_block_till_done()

    await hass.services.async_call(
        tts.DOMAIN,
        "yandextts_say",
        {"entity_id": "media_player.something", tts.ATTR_MESSAGE: "HomeAssistant"},
        blocking=True,
    )
    expect(len(calls)).to_equal(1)
    expect(
        await retrieve_media(hass, hass_client, calls[0].data[ATTR_MEDIA_CONTENT_ID])
    ).to_equal(HTTPStatus.OK)

    expect(len(aioclient_mock.mock_calls)).to_equal(1)


@test
async def service_say_russian_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test service call say."""
    calls = async_mock_service(hass, MP_DOMAIN, SERVICE_PLAY_MEDIA)

    url_param = {
        "text": "HomeAssistant",
        "lang": "ru-RU",
        "key": "1234567xx",
        "speaker": "zahar",
        "format": "mp3",
        "emotion": "neutral",
        "speed": 1,
    }
    aioclient_mock.get(URL, status=HTTPStatus.OK, content=b"test", params=url_param)

    config = {
        tts.DOMAIN: {
            "platform": "yandextts",
            "api_key": "1234567xx",
            "language": "ru-RU",
        }
    }

    with assert_setup_component(1, tts.DOMAIN):
        await async_setup_component(hass, tts.DOMAIN, config)
        await hass.async_block_till_done()

    await hass.services.async_call(
        tts.DOMAIN,
        "yandextts_say",
        {"entity_id": "media_player.something", tts.ATTR_MESSAGE: "HomeAssistant"},
        blocking=True,
    )

    expect(len(calls)).to_equal(1)
    expect(
        await retrieve_media(hass, hass_client, calls[0].data[ATTR_MEDIA_CONTENT_ID])
    ).to_equal(HTTPStatus.OK)

    expect(len(aioclient_mock.mock_calls)).to_equal(1)


@test
async def service_say_russian_service(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test service call say."""
    calls = async_mock_service(hass, MP_DOMAIN, SERVICE_PLAY_MEDIA)

    url_param = {
        "text": "HomeAssistant",
        "lang": "ru-RU",
        "key": "1234567xx",
        "speaker": "zahar",
        "format": "mp3",
        "emotion": "neutral",
        "speed": 1,
    }
    aioclient_mock.get(URL, status=HTTPStatus.OK, content=b"test", params=url_param)

    config = {tts.DOMAIN: {"platform": "yandextts", "api_key": "1234567xx"}}

    with assert_setup_component(1, tts.DOMAIN):
        await async_setup_component(hass, tts.DOMAIN, config)
        await hass.async_block_till_done()

    await hass.services.async_call(
        tts.DOMAIN,
        "yandextts_say",
        {
            "entity_id": "media_player.something",
            tts.ATTR_MESSAGE: "HomeAssistant",
            tts.ATTR_LANGUAGE: "ru-RU",
        },
        blocking=True,
    )
    expect(len(calls)).to_equal(1)
    expect(
        await retrieve_media(hass, hass_client, calls[0].data[ATTR_MEDIA_CONTENT_ID])
    ).to_equal(HTTPStatus.OK)

    expect(len(aioclient_mock.mock_calls)).to_equal(1)


@test
async def service_say_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test service call say."""
    calls = async_mock_service(hass, MP_DOMAIN, SERVICE_PLAY_MEDIA)

    url_param = {
        "text": "HomeAssistant",
        "lang": "en-US",
        "key": "1234567xx",
        "speaker": "zahar",
        "format": "mp3",
        "emotion": "neutral",
        "speed": 1,
    }
    aioclient_mock.get(
        URL,
        status=HTTPStatus.OK,
        exc=TimeoutError(),
        params=url_param,
    )

    config = {tts.DOMAIN: {"platform": "yandextts", "api_key": "1234567xx"}}

    with assert_setup_component(1, tts.DOMAIN):
        await async_setup_component(hass, tts.DOMAIN, config)
        await hass.async_block_till_done()

    await hass.services.async_call(
        tts.DOMAIN,
        "yandextts_say",
        {"entity_id": "media_player.something", tts.ATTR_MESSAGE: "HomeAssistant"},
        blocking=True,
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(
        await retrieve_media(hass, hass_client, calls[0].data[ATTR_MEDIA_CONTENT_ID])
    ).to_equal(HTTPStatus.INTERNAL_SERVER_ERROR)

    expect(len(aioclient_mock.mock_calls)).to_equal(1)


@test
async def service_say_http_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test service call say."""
    calls = async_mock_service(hass, MP_DOMAIN, SERVICE_PLAY_MEDIA)

    url_param = {
        "text": "HomeAssistant",
        "lang": "en-US",
        "key": "1234567xx",
        "speaker": "zahar",
        "format": "mp3",
        "emotion": "neutral",
        "speed": 1,
    }
    aioclient_mock.get(
        URL,
        status=HTTPStatus.FORBIDDEN,
        content=b"test",
        params=url_param,
    )

    config = {tts.DOMAIN: {"platform": "yandextts", "api_key": "1234567xx"}}

    with assert_setup_component(1, tts.DOMAIN):
        await async_setup_component(hass, tts.DOMAIN, config)
        await hass.async_block_till_done()

    await hass.services.async_call(
        tts.DOMAIN,
        "yandextts_say",
        {"entity_id": "media_player.something", tts.ATTR_MESSAGE: "HomeAssistant"},
        blocking=True,
    )

    expect(len(calls)).to_equal(1)
    expect(
        await retrieve_media(hass, hass_client, calls[0].data[ATTR_MEDIA_CONTENT_ID])
    ).to_equal(HTTPStatus.INTERNAL_SERVER_ERROR)


@test
async def service_say_specified_speaker(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test service call say."""
    calls = async_mock_service(hass, MP_DOMAIN, SERVICE_PLAY_MEDIA)

    url_param = {
        "text": "HomeAssistant",
        "lang": "en-US",
        "key": "1234567xx",
        "speaker": "alyss",
        "format": "mp3",
        "emotion": "neutral",
        "speed": 1,
    }
    aioclient_mock.get(URL, status=HTTPStatus.OK, content=b"test", params=url_param)

    config = {
        tts.DOMAIN: {
            "platform": "yandextts",
            "api_key": "1234567xx",
            "voice": "alyss",
        }
    }

    with assert_setup_component(1, tts.DOMAIN):
        await async_setup_component(hass, tts.DOMAIN, config)
        await hass.async_block_till_done()

    await hass.services.async_call(
        tts.DOMAIN,
        "yandextts_say",
        {"entity_id": "media_player.something", tts.ATTR_MESSAGE: "HomeAssistant"},
        blocking=True,
    )
    expect(len(calls)).to_equal(1)
    expect(
        await retrieve_media(hass, hass_client, calls[0].data[ATTR_MEDIA_CONTENT_ID])
    ).to_equal(HTTPStatus.OK)

    expect(len(aioclient_mock.mock_calls)).to_equal(1)


@test
async def service_say_specified_emotion(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test service call say."""
    calls = async_mock_service(hass, MP_DOMAIN, SERVICE_PLAY_MEDIA)

    url_param = {
        "text": "HomeAssistant",
        "lang": "en-US",
        "key": "1234567xx",
        "speaker": "zahar",
        "format": "mp3",
        "emotion": "evil",
        "speed": 1,
    }
    aioclient_mock.get(URL, status=HTTPStatus.OK, content=b"test", params=url_param)

    config = {
        tts.DOMAIN: {
            "platform": "yandextts",
            "api_key": "1234567xx",
            "emotion": "evil",
        }
    }

    with assert_setup_component(1, tts.DOMAIN):
        await async_setup_component(hass, tts.DOMAIN, config)
        await hass.async_block_till_done()

    await hass.services.async_call(
        tts.DOMAIN,
        "yandextts_say",
        {"entity_id": "media_player.something", tts.ATTR_MESSAGE: "HomeAssistant"},
        blocking=True,
    )
    expect(len(calls)).to_equal(1)
    expect(
        await retrieve_media(hass, hass_client, calls[0].data[ATTR_MEDIA_CONTENT_ID])
    ).to_equal(HTTPStatus.OK)

    expect(len(aioclient_mock.mock_calls)).to_equal(1)


@test
async def service_say_specified_low_speed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test service call say."""
    calls = async_mock_service(hass, MP_DOMAIN, SERVICE_PLAY_MEDIA)

    url_param = {
        "text": "HomeAssistant",
        "lang": "en-US",
        "key": "1234567xx",
        "speaker": "zahar",
        "format": "mp3",
        "emotion": "neutral",
        "speed": "0.1",
    }
    aioclient_mock.get(URL, status=HTTPStatus.OK, content=b"test", params=url_param)

    config = {
        tts.DOMAIN: {"platform": "yandextts", "api_key": "1234567xx", "speed": 0.1}
    }

    with assert_setup_component(1, tts.DOMAIN):
        await async_setup_component(hass, tts.DOMAIN, config)
        await hass.async_block_till_done()

    await hass.services.async_call(
        tts.DOMAIN,
        "yandextts_say",
        {"entity_id": "media_player.something", tts.ATTR_MESSAGE: "HomeAssistant"},
        blocking=True,
    )
    expect(len(calls)).to_equal(1)
    expect(
        await retrieve_media(hass, hass_client, calls[0].data[ATTR_MEDIA_CONTENT_ID])
    ).to_equal(HTTPStatus.OK)

    expect(len(aioclient_mock.mock_calls)).to_equal(1)


@test
async def service_say_specified_speed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test service call say."""
    calls = async_mock_service(hass, MP_DOMAIN, SERVICE_PLAY_MEDIA)

    url_param = {
        "text": "HomeAssistant",
        "lang": "en-US",
        "key": "1234567xx",
        "speaker": "zahar",
        "format": "mp3",
        "emotion": "neutral",
        "speed": 2,
    }
    aioclient_mock.get(URL, status=HTTPStatus.OK, content=b"test", params=url_param)

    config = {tts.DOMAIN: {"platform": "yandextts", "api_key": "1234567xx", "speed": 2}}

    with assert_setup_component(1, tts.DOMAIN):
        await async_setup_component(hass, tts.DOMAIN, config)
        await hass.async_block_till_done()

    await hass.services.async_call(
        tts.DOMAIN,
        "yandextts_say",
        {"entity_id": "media_player.something", tts.ATTR_MESSAGE: "HomeAssistant"},
        blocking=True,
    )
    expect(len(calls)).to_equal(1)
    expect(
        await retrieve_media(hass, hass_client, calls[0].data[ATTR_MEDIA_CONTENT_ID])
    ).to_equal(HTTPStatus.OK)

    expect(len(aioclient_mock.mock_calls)).to_equal(1)


@test
async def service_say_specified_options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test service call say with options."""
    calls = async_mock_service(hass, MP_DOMAIN, SERVICE_PLAY_MEDIA)

    url_param = {
        "text": "HomeAssistant",
        "lang": "en-US",
        "key": "1234567xx",
        "speaker": "zahar",
        "format": "mp3",
        "emotion": "evil",
        "speed": 2,
    }
    aioclient_mock.get(URL, status=HTTPStatus.OK, content=b"test", params=url_param)
    config = {tts.DOMAIN: {"platform": "yandextts", "api_key": "1234567xx"}}

    with assert_setup_component(1, tts.DOMAIN):
        await async_setup_component(hass, tts.DOMAIN, config)
        await hass.async_block_till_done()

    await hass.services.async_call(
        tts.DOMAIN,
        "yandextts_say",
        {
            "entity_id": "media_player.something",
            tts.ATTR_MESSAGE: "HomeAssistant",
            "options": {"emotion": "evil", "speed": 2},
        },
        blocking=True,
    )
    expect(len(calls)).to_equal(1)
    expect(
        await retrieve_media(hass, hass_client, calls[0].data[ATTR_MEDIA_CONTENT_ID])
    ).to_equal(HTTPStatus.OK)

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
