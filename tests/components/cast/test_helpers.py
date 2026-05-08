"""Tests for the Cast integration helpers."""

from aiohttp import client_exceptions
from tryke import Depends, expect, fixture, test

from homeassistant.components.cast.const import DOMAIN
from homeassistant.components.cast.helpers import (
    PlaylistError,
    PlaylistItem,
    PlaylistSupported,
    parse_playlist,
)
from homeassistant.core import HomeAssistant

from tests.common import async_load_fixture
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test.cases(
    test.case(
        "bbc_radio_no_content_type",
        url="http://a.files.bbci.co.uk/media/live/manifesto/audio/simulcast/hls/nonuk/sbr_low/ak/bbc_radio_fourfm.m3u8",
        fixture_name="bbc_radio_fourfm.m3u8",
        content_type=None,
    ),
    test.case(
        "rthkaudio2_with_content_type",
        url="https://rthkaudio2-lh.akamaihd.net/i/radio2_1@355865/master.m3u8",
        fixture_name="rthkaudio2.m3u8",
        content_type="application/vnd.apple.mpegurl",
    ),
    test.case(
        "rthkaudio2_no_content_type",
        url="https://rthkaudio2-lh.akamaihd.net/i/radio2_1@355865/master.m3u8",
        fixture_name="rthkaudio2.m3u8",
        content_type=None,
    ),
)
async def hls_playlist_supported(
    *,
    url: str,
    fixture_name: str,
    content_type: str | None,
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test playlist parsing of HLS playlist."""
    headers = {"content-type": content_type}
    aioclient_mock.get(
        url,
        text=await async_load_fixture(hass, fixture_name, DOMAIN),
        headers=headers,
    )
    async with expect_raises_async(PlaylistSupported):
        await parse_playlist(hass, url)


@test.cases(
    test.case(
        "m3u_extinf",
        url="https://sverigesradio.se/topsy/direkt/209-hi-mp3.m3u",
        fixture_name="209-hi-mp3.m3u",
        content_type="audio/x-mpegurl",
        expected_playlist=[
            PlaylistItem(
                length=["-1"],
                title="Sveriges Radio",
                url="https://http-live.sr.se/p4norrbotten-mp3-192",
            )
        ],
    ),
    test.case(
        "m3u_bad_extinf",
        url="https://sverigesradio.se/topsy/direkt/209-hi-mp3.m3u",
        fixture_name="209-hi-mp3_bad_extinf.m3u",
        content_type="audio/x-mpegurl",
        expected_playlist=[
            PlaylistItem(
                length=None,
                title=None,
                url="https://http-live.sr.se/p4norrbotten-mp3-192",
            )
        ],
    ),
    test.case(
        "m3u_no_extinf",
        url="https://sverigesradio.se/topsy/direkt/209-hi-mp3.m3u",
        fixture_name="209-hi-mp3_no_extinf.m3u",
        content_type="audio/x-mpegurl",
        expected_playlist=[
            PlaylistItem(
                length=None,
                title=None,
                url="https://http-live.sr.se/p4norrbotten-mp3-192",
            )
        ],
    ),
    test.case(
        "pls",
        url="http://sverigesradio.se/topsy/direkt/164-hi-aac.pls",
        fixture_name="164-hi-aac.pls",
        content_type="audio/x-mpegurl",
        expected_playlist=[
            PlaylistItem(
                length="-1",
                title="Sveriges Radio",
                url="https://http-live.sr.se/p3-aac-192",
            )
        ],
    ),
)
async def parse_playlist_test(
    *,
    url: str,
    fixture_name: str,
    content_type: str,
    expected_playlist: list[PlaylistItem],
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test playlist parsing of HLS playlist."""
    headers = {"content-type": content_type}
    aioclient_mock.get(
        url,
        text=await async_load_fixture(hass, fixture_name, DOMAIN),
        headers=headers,
    )
    playlist = await parse_playlist(hass, url)
    expect(playlist).to_equal(expected_playlist)


@test.cases(
    test.case(
        "invalid_entries",
        url="http://sverigesradio.se/164-hi-aac.pls",
        fixture_name="164-hi-aac_invalid_entries.pls",
    ),
    test.case(
        "invalid_file",
        url="http://sverigesradio.se/164-hi-aac.pls",
        fixture_name="164-hi-aac_invalid_file.pls",
    ),
    test.case(
        "invalid_version",
        url="http://sverigesradio.se/164-hi-aac.pls",
        fixture_name="164-hi-aac_invalid_version.pls",
    ),
    test.case(
        "invalid",
        url="http://sverigesradio.se/164-hi-aac.pls",
        fixture_name="164-hi-aac_invalid.pls",
    ),
    test.case(
        "missing_file",
        url="http://sverigesradio.se/164-hi-aac.pls",
        fixture_name="164-hi-aac_missing_file.pls",
    ),
    test.case(
        "no_entries",
        url="http://sverigesradio.se/164-hi-aac.pls",
        fixture_name="164-hi-aac_no_entries.pls",
    ),
    test.case(
        "no_playlist",
        url="http://sverigesradio.se/164-hi-aac.pls",
        fixture_name="164-hi-aac_no_playlist.pls",
    ),
    test.case(
        "no_version",
        url="http://sverigesradio.se/164-hi-aac.pls",
        fixture_name="164-hi-aac_no_version.pls",
    ),
    test.case(
        "bad_url",
        url="https://sverigesradio.se/209-hi-mp3.m3u",
        fixture_name="209-hi-mp3_bad_url.m3u",
    ),
    test.case(
        "empty_m3u",
        url="https://sverigesradio.se/209-hi-mp3.m3u",
        fixture_name="empty.m3u",
    ),
)
async def parse_bad_playlist(
    *,
    url: str,
    fixture_name: str,
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test playlist parsing of HLS playlist."""
    aioclient_mock.get(url, text=await async_load_fixture(hass, fixture_name, DOMAIN))
    async with expect_raises_async(PlaylistError):
        await parse_playlist(hass, url)


@test.cases(
    test.case(
        "timeout",
        url="http://sverigesradio.se/164-hi-aac.pls",
        exc=TimeoutError,
    ),
    test.case(
        "client_error",
        url="http://sverigesradio.se/164-hi-aac.pls",
        exc=client_exceptions.ClientError,
    ),
)
async def parse_http_error(
    *,
    url: str,
    exc: type[Exception],
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test playlist parsing of HLS playlist when aioclient raises."""
    aioclient_mock.get(url, text="", exc=exc)
    async with expect_raises_async(PlaylistError):
        await parse_playlist(hass, url)
