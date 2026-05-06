"""Tryke fixtures for Flo tests."""

from http import HTTPStatus
import json
import time

from tryke import Depends, fixture

from homeassistant.const import CONTENT_TYPE_JSON

from .common import TEST_EMAIL_ADDRESS, TEST_TOKEN, TEST_USER_ID

from tests.common import load_fixture
from tests.hass_fixtures import aioclient_mock as aioclient_mock_fixture
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def aioclient_mock_setup(
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> AiohttpClientMocker:
    """Fixture to provide an aioclient mocker preloaded with flo responses."""
    now = round(time.time())
    aioclient_mock.post(
        "https://api.meetflo.com/api/v1/users/auth",
        text=json.dumps(
            {
                "token": TEST_TOKEN,
                "tokenPayload": {
                    "user": {"user_id": TEST_USER_ID, "email": TEST_EMAIL_ADDRESS},
                    "timestamp": now,
                },
                "tokenExpiration": 86400,
                "timeNow": now,
            }
        ),
        headers={"Content-Type": CONTENT_TYPE_JSON},
        status=HTTPStatus.OK,
    )
    aioclient_mock.post(
        "https://api-gw.meetflo.com/api/v2/presence/me",
        text=load_fixture("flo/ping_response.json"),
        headers={"Content-Type": CONTENT_TYPE_JSON},
        status=HTTPStatus.OK,
    )
    aioclient_mock.get(
        "https://api-gw.meetflo.com/api/v2/devices/98765",
        text=load_fixture("flo/device_info_response.json"),
        status=HTTPStatus.OK,
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )
    aioclient_mock.get(
        "https://api-gw.meetflo.com/api/v2/users/12345abcde",
        text=load_fixture("flo/user_info_expand_locations_response.json"),
        status=HTTPStatus.OK,
        headers={"Content-Type": CONTENT_TYPE_JSON},
        params={"expand": "locations"},
    )
    aioclient_mock.get(
        "https://api-gw.meetflo.com/api/v2/users/12345abcde",
        text=load_fixture("flo/user_info_expand_locations_response.json"),
        status=HTTPStatus.OK,
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )
    return aioclient_mock
