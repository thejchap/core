"""Test media browser helpers for media player."""

from collections.abc import Generator
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.media_player.browse_media import (
    async_process_play_media_url,
)
from homeassistant.core import HomeAssistant
from homeassistant.core_config import async_process_ha_core_config
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.network import NoURLAvailableError

from tests.common import mock_component
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network=Depends(mock_network)) -> int:
    return 0


@fixture
def mock_sign_path() -> Generator[None]:
    """Mock sign path."""
    with patch(
        "homeassistant.components.media_player.browse_media.async_sign_path",
        side_effect=lambda _, url, _2: url + "?authSig=bla",
    ):
        yield


@test
async def process_play_media_url(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_sign_path: None = Depends(mock_sign_path),
) -> None:
    """Test it prefixes and signs urls."""
    await async_process_ha_core_config(
        hass,
        {"internal_url": "http://example.local:8123"},
    )
    hass.config.api = Mock(use_ssl=False, port=8123, local_ip="192.168.123.123")

    # Not changing a url that is not a hass url
    expect(
        async_process_play_media_url(hass, "https://not-hass.com/path")
    ).to_equal("https://not-hass.com/path")
    # Not changing a url that is not http/https
    expect(
        async_process_play_media_url(hass, "file:///tmp/test.mp3")
    ).to_equal("file:///tmp/test.mp3")

    # Testing signing hass URLs
    expect(async_process_play_media_url(hass, "/path")).to_equal(
        "http://example.local:8123/path?authSig=bla"
    )
    expect(
        async_process_play_media_url(hass, "http://example.local:8123/path")
    ).to_equal("http://example.local:8123/path?authSig=bla")
    expect(
        async_process_play_media_url(hass, "http://192.168.123.123:8123/path")
    ).to_equal("http://192.168.123.123:8123/path?authSig=bla")
    with patch(
        "homeassistant.components.media_player.browse_media.get_url",
        side_effect=NoURLAvailableError,
    ):
        expect(lambda: async_process_play_media_url(hass, "/path")).to_raise(
            HomeAssistantError
        )

    # Test skip signing URLs that have a query param
    expect(async_process_play_media_url(hass, "/path?hello=world")).to_equal(
        "http://example.local:8123/path?hello=world"
    )
    expect(
        async_process_play_media_url(
            hass, "http://192.168.123.123:8123/path?hello=world"
        )
    ).to_equal("http://192.168.123.123:8123/path?hello=world")

    # Test skip signing URLs if they are known to require no auth
    expect(async_process_play_media_url(hass, "/api/tts_proxy/bla")).to_equal(
        "http://example.local:8123/api/tts_proxy/bla"
    )
    expect(
        async_process_play_media_url(
            hass, "http://example.local:8123/api/tts_proxy/bla"
        )
    ).to_equal("http://example.local:8123/api/tts_proxy/bla")

    # Not changing a URL which is not absolute and does not start with /
    expect(async_process_play_media_url(hass, "hello")).to_equal("hello")


@test
async def process_play_media_url_for_addon(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_sign_path: None = Depends(mock_sign_path),
) -> None:
    """Test it uses the hostname for an addon if available."""
    await async_process_ha_core_config(
        hass,
        {
            "internal_url": "http://example.local:8123",
            "external_url": "https://example.com",
        },
    )

    # Not hassio or hassio not loaded yet, don't use supervisor network url
    hass.config.api = Mock(use_ssl=False, port=8123, local_ip="192.168.123.123")
    expect(
        async_process_play_media_url(hass, "/path", for_supervisor_network=True)
    ).not_.to_equal("http://homeassistant:8123/path?authSig=bla")

    # Is hassio and not SSL, use an supervisor network url
    mock_component(hass, "hassio")
    expect(
        async_process_play_media_url(hass, "/path", for_supervisor_network=True)
    ).to_equal("http://homeassistant:8123/path?authSig=bla")

    # Hassio loaded but using SSL, don't use an supervisor network url
    hass.config.api = Mock(use_ssl=True, port=8123, local_ip="192.168.123.123")
    expect(
        async_process_play_media_url(hass, "/path", for_supervisor_network=True)
    ).not_.to_equal("https://homeassistant:8123/path?authSig=bla")
