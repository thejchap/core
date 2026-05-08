"""Test Discord notify."""

import logging
from http import HTTPStatus

from tryke import Depends, expect, fixture, test

from homeassistant.components.discord.notify import DiscordNotificationService
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import LogCapture, aioclient_mock as aioclient_mock_fixture, caplog as caplog_fixture, hass as hass_fixture, mock_network
from tests.test_util.aiohttp import AiohttpClientMocker


MESSAGE = "Testing Discord Messenger platform"
CONTENT = b"TestContent"
URL_ATTACHMENT = "http://127.0.0.1:8080/image.jpg"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@fixture
def discord_notification_service(
    hass: HomeAssistant = Depends(hass_fixture),
) -> DiscordNotificationService:
    """Set up discord notification service."""
    hass.config.allowlist_external_urls.add(URL_ATTACHMENT)
    return DiscordNotificationService(hass, "token")


def _make_aiohttp_factory(aioclient_mock: AiohttpClientMocker):
    def _factory(headers: dict[str, str] | None = None) -> AiohttpClientMocker:
        if headers is not None:
            aioclient_mock.get(
                URL_ATTACHMENT, status=HTTPStatus.OK, content=CONTENT, headers=headers
            )
        else:
            aioclient_mock.get(
                URL_ATTACHMENT,
                status=HTTPStatus.OK,
                content=CONTENT,
            )
        return aioclient_mock
    return _factory


@test
async def send_message_without_target_logs_error(
    _t: HomeAssistant = Depends(_trigger_executor),
    discord_notification_service: DiscordNotificationService = Depends(discord_notification_service),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test send message."""
    factory = _make_aiohttp_factory(aioclient_mock)
    discord_aiohttp_mock = factory()
    with caplog.at_level(
        logging.ERROR, logger="homeassistant.components.discord.notify"
    ):
        await discord_notification_service.async_send_message(MESSAGE)
    expect("No target specified" in caplog.text).to_be(True)
    expect(discord_aiohttp_mock.call_count).to_equal(0)


@test
async def get_file_from_url(
    _t: HomeAssistant = Depends(_trigger_executor),
    discord_notification_service: DiscordNotificationService = Depends(discord_notification_service),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test getting a file from a URL."""
    factory = _make_aiohttp_factory(aioclient_mock)
    headers = {"Content-Length": str(len(CONTENT))}
    discord_aiohttp_mock = factory(headers)
    result = await discord_notification_service.async_get_file_from_url(
        URL_ATTACHMENT, True, len(CONTENT)
    )

    expect(discord_aiohttp_mock.call_count).to_equal(1)
    expect(result).to_equal(bytearray(CONTENT))


@test
async def get_file_from_url_not_on_allowlist(
    _t: HomeAssistant = Depends(_trigger_executor),
    discord_notification_service: DiscordNotificationService = Depends(discord_notification_service),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test getting file from URL that isn't on the allowlist."""
    url = "http://dodgyurl.com"
    with caplog.at_level(
        logging.WARNING, logger="homeassistant.components.discord.notify"
    ):
        result = await discord_notification_service.async_get_file_from_url(
            url, True, len(CONTENT)
        )

    expect(f"URL not allowed: {url}" in caplog.text).to_be(True)
    expect(result).to_be(None)


@test
async def get_file_from_url_with_large_attachment(
    _t: HomeAssistant = Depends(_trigger_executor),
    discord_notification_service: DiscordNotificationService = Depends(discord_notification_service),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test getting file from URL with large attachment (per Content-Length header) throws error."""
    factory = _make_aiohttp_factory(aioclient_mock)
    headers = {"Content-Length": str(len(CONTENT) + 1)}
    discord_aiohttp_mock = factory(headers)
    with caplog.at_level(
        logging.WARNING, logger="homeassistant.components.discord.notify"
    ):
        result = await discord_notification_service.async_get_file_from_url(
            URL_ATTACHMENT, True, len(CONTENT)
        )

    expect(discord_aiohttp_mock.call_count).to_equal(1)
    expect("Attachment too large (Content-Length reports" in caplog.text).to_be(True)
    expect(result).to_be(None)


@test
async def get_file_from_url_with_large_attachment_no_header(
    _t: HomeAssistant = Depends(_trigger_executor),
    discord_notification_service: DiscordNotificationService = Depends(discord_notification_service),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test getting file from URL with large attachment (per content length) throws error."""
    factory = _make_aiohttp_factory(aioclient_mock)
    discord_aiohttp_mock = factory()
    with caplog.at_level(
        logging.WARNING, logger="homeassistant.components.discord.notify"
    ):
        result = await discord_notification_service.async_get_file_from_url(
            URL_ATTACHMENT, True, len(CONTENT) - 1
        )

    expect(discord_aiohttp_mock.call_count).to_equal(1)
    expect("Attachment too large (Stream reports" in caplog.text).to_be(True)
    expect(result).to_be(None)
