"""The tests for the MaryTTS speech platform."""

from collections.abc import Generator
from http import HTTPStatus
import io
from pathlib import Path
from unittest.mock import patch
import wave

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
    hass as hass_fixture,
    hass_client as hass_client_fixture,
    mock_network,
    tmp_path as tmp_path_fixture,
)
from tests.typing import ClientSessionGenerator


def get_empty_wav() -> bytes:
    """Get bytes for empty WAV file."""
    with io.BytesIO() as wav_io:
        with wave.open(wav_io, "wb") as wav_file:
            wav_file.setframerate(22050)
            wav_file.setsampwidth(2)
            wav_file.setnchannels(1)

        return wav_io.getvalue()


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
def _trigger_executor(
    _network: None = Depends(mock_network),
    _cache: None = Depends(mock_tts_cache_dir),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def setup_component(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup component."""
    config = {tts.DOMAIN: {"platform": "marytts"}}

    with assert_setup_component(1, tts.DOMAIN):
        await async_setup_component(hass, tts.DOMAIN, config)
        await hass.async_block_till_done()


@test
async def service_say(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test service call say."""
    calls = async_mock_service(hass, MP_DOMAIN, SERVICE_PLAY_MEDIA)

    config = {tts.DOMAIN: {"platform": "marytts"}}

    with assert_setup_component(1, tts.DOMAIN):
        await async_setup_component(hass, tts.DOMAIN, config)
        await hass.async_block_till_done()

    with patch(
        "homeassistant.components.marytts.tts.MaryTTS.speak",
        return_value=get_empty_wav(),
    ) as mock_speak:
        await hass.services.async_call(
            tts.DOMAIN,
            "marytts_say",
            {
                "entity_id": "media_player.something",
                tts.ATTR_MESSAGE: "HomeAssistant",
            },
            blocking=True,
        )

        expect(
            await retrieve_media(
                hass, hass_client, calls[0].data[ATTR_MEDIA_CONTENT_ID]
            )
        ).to_equal(HTTPStatus.OK)

    mock_speak.assert_called_once()
    mock_speak.assert_called_with("HomeAssistant", {})

    expect(len(calls)).to_equal(1)


@test
async def service_say_with_effect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test service call say with effects."""
    calls = async_mock_service(hass, MP_DOMAIN, SERVICE_PLAY_MEDIA)

    config = {tts.DOMAIN: {"platform": "marytts", "effect": {"Volume": "amount:2.0;"}}}

    with assert_setup_component(1, tts.DOMAIN):
        await async_setup_component(hass, tts.DOMAIN, config)
        await hass.async_block_till_done()

    with patch(
        "homeassistant.components.marytts.tts.MaryTTS.speak",
        return_value=get_empty_wav(),
    ) as mock_speak:
        await hass.services.async_call(
            tts.DOMAIN,
            "marytts_say",
            {
                "entity_id": "media_player.something",
                tts.ATTR_MESSAGE: "HomeAssistant",
            },
            blocking=True,
        )

        expect(
            await retrieve_media(
                hass, hass_client, calls[0].data[ATTR_MEDIA_CONTENT_ID]
            )
        ).to_equal(HTTPStatus.OK)

    mock_speak.assert_called_once()
    mock_speak.assert_called_with("HomeAssistant", {"Volume": "amount:2.0;"})

    expect(len(calls)).to_equal(1)


@test
async def service_say_http_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test service call say."""
    calls = async_mock_service(hass, MP_DOMAIN, SERVICE_PLAY_MEDIA)

    config = {tts.DOMAIN: {"platform": "marytts"}}

    with assert_setup_component(1, tts.DOMAIN):
        await async_setup_component(hass, tts.DOMAIN, config)
        await hass.async_block_till_done()

    with patch(
        "homeassistant.components.marytts.tts.MaryTTS.speak",
        side_effect=Exception(),
    ) as mock_speak:
        await hass.services.async_call(
            tts.DOMAIN,
            "marytts_say",
            {
                "entity_id": "media_player.something",
                tts.ATTR_MESSAGE: "HomeAssistant",
            },
        )
        await hass.async_block_till_done()

        expect(
            await retrieve_media(
                hass, hass_client, calls[0].data[ATTR_MEDIA_CONTENT_ID]
            )
        ).to_equal(HTTPStatus.INTERNAL_SERVER_ERROR)

    mock_speak.assert_called_once()
