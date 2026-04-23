"""The test for the Facebook notify module."""

import base64
from http import HTTPStatus
import logging
from unittest.mock import patch

import requests_mock as requests_mock_lib
from tryke import Depends, expect, fixture, test

from homeassistant.components import notify
from homeassistant.components.clicksend_tts import notify as cs_tts
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import assert_setup_component
from tests.hass_fixtures import LogCapture, caplog, hass

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
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


async def setup_notify(hass: HomeAssistant) -> None:
    """Test setup."""
    with assert_setup_component(1, notify.DOMAIN) as config:
        expect(await async_setup_component(hass, notify.DOMAIN, CONFIG)).to_be(True)
        expect(bool(config[notify.DOMAIN])).to_be(True)
        await hass.async_block_till_done()


@test
async def no_notify_service(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test missing platform notify service instance."""
    caplog.set_level(logging.ERROR)
    with patch(
        "homeassistant.components.clicksend_tts.notify.get_service", autospec=True
    ) as mock_clicksend_tts_notify:
        mock_clicksend_tts_notify.return_value = None
        await setup_notify(hass)
        await hass.async_block_till_done()
        expect(mock_clicksend_tts_notify.called).to_be(True)
        expect(
            "Failed to initialize notification service clicksend_tts" in caplog.text
        ).to_be(True)


@test
async def send_simple_message(hass: HomeAssistant = Depends(hass)) -> None:
    """Test sending a simple message with success."""

    with requests_mock_lib.Mocker() as mock:
        mock.get(
            f"{cs_tts.BASE_API_URL}/account",
            status_code=HTTPStatus.OK,
        )

        mock.post(
            f"{cs_tts.BASE_API_URL}/voice/send",
            status_code=HTTPStatus.OK,
        )

        await setup_notify(hass)

        data = {
            notify.ATTR_MESSAGE: TEST_MESSAGE,
        }
        await hass.services.async_call(
            notify.DOMAIN, cs_tts.DEFAULT_NAME, data, blocking=True
        )

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
