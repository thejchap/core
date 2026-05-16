"""Tryke fixtures for signal_messenger tests."""

from __future__ import annotations

from collections.abc import Callable, Generator
from http import HTTPStatus

from pysignalclirestapi import SignalCliRestApi
from requests_mock import Mocker
from tryke import Depends, fixture

from homeassistant.components.signal_messenger.notify import SignalNotificationService
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import requests_mock_session

SIGNAL_SEND_PATH_SUFIX = "/v2/send"
MESSAGE = "Testing Signal Messenger platform :)"
CONTENT = b"TestContent"
NUMBER_FROM = "+43443434343"
NUMBERS_TO = ["+435565656565"]
URL_ATTACHMENT = "http://127.0.0.1:8080/image.jpg"


@fixture
def signal_notification_service(
    hass: HomeAssistant = Depends(hass_fixture),
) -> SignalNotificationService:
    """Set up signal notification service."""
    hass.config.allowlist_external_urls.add(URL_ATTACHMENT)
    recipients = ["+435565656565"]
    number = "+43443434343"
    client = SignalCliRestApi("http://127.0.0.1:8080", number)
    return SignalNotificationService(hass, recipients, client)


@fixture
def signal_requests_mock_factory(
    requests_mock: Mocker = Depends(requests_mock_session),
) -> Callable[..., Mocker]:
    """Create signal service mock from factory."""

    def _signal_requests_mock_factory(
        success_send_result: bool = True, content_length_header: str | None = None
    ) -> Mocker:
        requests_mock.register_uri(
            "GET",
            "http://127.0.0.1:8080/v1/about",
            status_code=HTTPStatus.OK,
            json={"versions": ["v1", "v2"]},
        )
        if success_send_result:
            requests_mock.register_uri(
                "POST",
                "http://127.0.0.1:8080" + SIGNAL_SEND_PATH_SUFIX,
                status_code=HTTPStatus.CREATED,
            )
        else:
            requests_mock.register_uri(
                "POST",
                "http://127.0.0.1:8080" + SIGNAL_SEND_PATH_SUFIX,
                status_code=HTTPStatus.BAD_REQUEST,
            )
        if content_length_header is not None:
            requests_mock.register_uri(
                "GET",
                URL_ATTACHMENT,
                status_code=HTTPStatus.OK,
                content=CONTENT,
                headers={"Content-Length": content_length_header},
            )
        else:
            requests_mock.register_uri(
                "GET",
                URL_ATTACHMENT,
                status_code=HTTPStatus.OK,
                content=CONTENT,
            )
        return requests_mock

    return _signal_requests_mock_factory
