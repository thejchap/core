"""The test for the Clicksend TTS notify module."""

import base64
from http import HTTPStatus
import logging
from unittest.mock import MagicMock

import requests_mock
from tryke import Depends, expect, fixture, test

from homeassistant.components import notify
from homeassistant.components.clicksend_tts import notify as cs_tts
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import mock_clicksend_tts_notify

from tests.common import assert_setup_component
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)

# Infos from https://developers.clicksend.com/docs/rest/v3/#testing
TEST_USERNAME = "nocredit"
TEST_API_KEY = "D83DED51-9E35-4D42-9BB9-0E34B7CA85AE"
TEST_VOICE_NUMBER = "+61411111111"

TEST_VOICE = "male"
TEST_LANGUAGE = "fr-fr"
TEST_MESSAGE = "Just a test message!"


CONFIG = {
    notify.DOMAIN: {
        "platform": "clicksend_tts",
        cs_tts.CONF_USERNAME: TEST_USERNAME,
        cs_tts.CONF_API_KEY: TEST_API_KEY,
        cs_tts.CONF_RECIPIENT: TEST_VOICE_NUMBER,
        cs_tts.CONF_LANGUAGE: TEST_LANGUAGE,
        cs_tts.CONF_VOICE: TEST_VOICE,
    }
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


async def setup_notify(hass: HomeAssistant) -> None:
    """Test setup."""
    with assert_setup_component(1, notify.DOMAIN) as config:
        assert await async_setup_component(hass, notify.DOMAIN, CONFIG)
        assert config[notify.DOMAIN]
        await hass.async_block_till_done()


@test
async def no_notify_service(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_notify: MagicMock = Depends(mock_clicksend_tts_notify),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test missing platform notify service instance."""
    caplog.set_level(logging.ERROR)
    mock_notify.return_value = None
    await setup_notify(hass)
    await hass.async_block_till_done()
    expect(mock_notify.called).to_be(True)
    expect(
        "Failed to initialize notification service clicksend_tts" in caplog.text
    ).to_be(True)


@test
async def send_simple_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test sending a simple message with success."""
    with requests_mock.Mocker() as mock:
        # Mocking authentication endpoint
        mock.get(
            f"{cs_tts.BASE_API_URL}/account",
            status_code=HTTPStatus.OK,
        )

        # Mocking TTS endpoint
        mock.post(
            f"{cs_tts.BASE_API_URL}/voice/send",
            status_code=HTTPStatus.OK,
        )

        # Setting up integration
        await setup_notify(hass)

        # Sending message
        data = {
            notify.ATTR_MESSAGE: TEST_MESSAGE,
        }
        await hass.services.async_call(
            notify.DOMAIN, cs_tts.DEFAULT_NAME, data, blocking=True
        )

        # Checking if everything went well
        expect(mock.called).to_be(True)
        expect(mock.call_count).to_equal(2)

        expected_body = {
            "messages": [
                {
                    "source": "hass.notify",
                    "to": TEST_VOICE_NUMBER,
                    "body": TEST_MESSAGE,
                    "lang": TEST_LANGUAGE,
                    "voice": TEST_VOICE,
                }
            ]
        }
        expect(mock.last_request.json()).to_equal(expected_body)

        expected_content_type = "application/json"
        expect("Content-Type" in mock.last_request.headers).to_be(True)
        expect(mock.last_request.headers["Content-Type"]).to_equal(
            expected_content_type
        )

        encoded_auth = base64.b64encode(
            f"{TEST_USERNAME}:{TEST_API_KEY}".encode()
        ).decode()
        expected_auth = f"Basic {encoded_auth}"
        expect("Authorization" in mock.last_request.headers).to_be(True)
        expect(mock.last_request.headers["Authorization"]).to_equal(expected_auth)


_ = (mock_clicksend_tts_notify,)
