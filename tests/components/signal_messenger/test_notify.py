"""The tests for the signal_messenger platform."""

from __future__ import annotations

import base64
import json
import logging
import os
import tempfile
from unittest.mock import patch

# ``requests`` honours REQUESTS_CA_BUNDLE / SSL_CERT_FILE by rewriting
# ``verify=True`` into that path inside ``merge_environment_settings``
# before the request is fired. ``requests_mock`` records the post-merge
# value on ``last_request.verify``, so harness envs that set these vars
# break the ``verify is True`` assertions below. Patch them out per-test
# via ``patch.dict(os.environ, ...)``.
_VERIFY_ENV_CLEAR = {"REQUESTS_CA_BUNDLE": "", "SSL_CERT_FILE": "", "CURL_CA_BUNDLE": ""}

from pysignalclirestapi.api import SignalCliRestApiError
from requests_mock.mocker import Mocker
from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant.components.signal_messenger.notify import SignalNotificationService
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import (
    CONTENT,
    MESSAGE,
    NUMBER_FROM,
    NUMBERS_TO,
    SIGNAL_SEND_PATH_SUFIX,
    URL_ATTACHMENT,
    signal_notification_service as signal_notification_service_fx,
    signal_requests_mock_factory as signal_requests_mock_factory_fx,
)

from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)

BASE_COMPONENT = "notify"


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> int:
    """Module-level anchor fixture."""
    return 0


def _assert_sending_requests(
    signal_requests_mock_factory: Mocker,
    attachments_num: int = 0,
    recipients: list[str] | None = None,
) -> None:
    """Assert message was send with correct parameters."""
    send_request = signal_requests_mock_factory.request_history[-1]
    expect(send_request.path).to_equal(SIGNAL_SEND_PATH_SUFIX)

    body_request = json.loads(send_request.text)
    expect(body_request["message"]).to_equal(MESSAGE)
    expect(body_request["number"]).to_equal(NUMBER_FROM)
    expect(body_request["recipients"]).to_equal(recipients or NUMBERS_TO)
    expect(len(body_request["base64_attachments"])).to_equal(attachments_num)

    for attachment in body_request["base64_attachments"]:
        if len(attachment) > 0:
            expect(base64.b64decode(attachment)).to_equal(CONTENT)


@test
async def signal_messenger_init(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that service loads successfully."""
    config = {
        BASE_COMPONENT: {
            "name": "test",
            "platform": "signal_messenger",
            "url": "http://127.0.0.1:8080",
            "number": NUMBER_FROM,
            "recipients": NUMBERS_TO,
        }
    }

    with patch("pysignalclirestapi.SignalCliRestApi.send_message", return_value=None):
        expect(await async_setup_component(hass, BASE_COMPONENT, config)).to_be(True)
        await hass.async_block_till_done()

        expect(hass.services.has_service(BASE_COMPONENT, "test")).to_be(True)


@test
async def send_message(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
    signal_requests_mock_factory: Mocker = Depends(signal_requests_mock_factory_fx),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test send message."""
    signal_requests_mock = signal_requests_mock_factory()
    with caplog.at_level(
        logging.DEBUG, logger="homeassistant.components.signal_messenger.notify"
    ):
        signal_notification_service.send_message(MESSAGE)
    expect("Sending signal message" in caplog.text).to_be(True)
    expect(signal_requests_mock.called).to_be(True)
    expect(signal_requests_mock.call_count).to_equal(2)
    _assert_sending_requests(signal_requests_mock)


@test
async def send_message_with_custom_recipients(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
    signal_requests_mock_factory: Mocker = Depends(signal_requests_mock_factory_fx),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test send message with custom recipients."""
    signal_requests_mock = signal_requests_mock_factory()
    with caplog.at_level(
        logging.DEBUG, logger="homeassistant.components.signal_messenger.notify"
    ):
        signal_notification_service.send_message(
            MESSAGE, target=["+49111111111", "+49222222222"]
        )
    expect("Sending signal message" in caplog.text).to_be(True)
    expect(signal_requests_mock.called).to_be(True)
    expect(signal_requests_mock.call_count).to_equal(2)
    _assert_sending_requests(
        signal_requests_mock, recipients=["+49111111111", "+49222222222"]
    )


@test
async def send_message_styled(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
    signal_requests_mock_factory: Mocker = Depends(signal_requests_mock_factory_fx),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test send styled message."""
    signal_requests_mock = signal_requests_mock_factory()
    with caplog.at_level(
        logging.DEBUG, logger="homeassistant.components.signal_messenger.notify"
    ):
        data = {"text_mode": "styled"}
        signal_notification_service.send_message(MESSAGE, data=data)
    post_data = json.loads(signal_requests_mock.request_history[-1].text)
    expect("Sending signal message" in caplog.text).to_be(True)
    expect(signal_requests_mock.called).to_be(True)
    expect(signal_requests_mock.call_count).to_equal(2)
    expect(post_data["text_mode"]).to_equal("styled")
    _assert_sending_requests(signal_requests_mock)


@test
async def send_message_to_api_with_bad_data_throws_error(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
    signal_requests_mock_factory: Mocker = Depends(signal_requests_mock_factory_fx),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test sending a message with bad data to the API throws an error."""
    signal_requests_mock = signal_requests_mock_factory(False)
    with caplog.at_level(
        logging.DEBUG, logger="homeassistant.components.signal_messenger.notify"
    ):
        expect(lambda: signal_notification_service.send_message(MESSAGE)).to_raise(
            SignalCliRestApiError, match="Couldn't send signal message"
        )

    expect("Sending signal message" in caplog.text).to_be(True)
    expect(signal_requests_mock.called).to_be(True)
    expect(signal_requests_mock.call_count).to_equal(2)


@test
async def send_message_with_bad_data_throws_vol_error(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
    signal_requests_mock_factory: Mocker = Depends(signal_requests_mock_factory_fx),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test sending a message with bad data throws an error."""
    with caplog.at_level(
        logging.DEBUG, logger="homeassistant.components.signal_messenger.notify"
    ):
        expect(
            lambda: signal_notification_service.send_message(
                MESSAGE, data={"test": "test"}
            )
        ).to_raise(vol.Invalid, match="extra keys not allowed")

    expect("Sending signal message" in caplog.text).to_be(True)


@test
async def send_message_styled_with_bad_data_throws_vol_error(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
    signal_requests_mock_factory: Mocker = Depends(signal_requests_mock_factory_fx),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test sending a styled message with bad data throws an error."""
    with caplog.at_level(
        logging.DEBUG, logger="homeassistant.components.signal_messenger.notify"
    ):
        expect(
            lambda: signal_notification_service.send_message(
                MESSAGE, data={"text_mode": "test"}
            )
        ).to_raise(
            vol.Invalid,
            match=(
                r"value must be one of \['normal', 'styled'\] for "
                r"dictionary value @ data\['text_mode'\]"
            ),
        )

    expect("Sending signal message" in caplog.text).to_be(True)


@test
async def send_message_with_attachment(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
    signal_requests_mock_factory: Mocker = Depends(signal_requests_mock_factory_fx),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test send message with attachment."""
    signal_requests_mock = signal_requests_mock_factory()
    with (
        caplog.at_level(
            logging.DEBUG, logger="homeassistant.components.signal_messenger.notify"
        ),
        tempfile.NamedTemporaryFile(
            mode="w", suffix=".png", prefix=os.path.basename(__file__)
        ) as temp_file,
    ):
        temp_file.write("attachment_data")
        data = {"attachments": [temp_file.name]}
        signal_notification_service.send_message(MESSAGE, data=data)

    expect("Sending signal message" in caplog.text).to_be(True)
    expect(signal_requests_mock.called).to_be(True)
    expect(signal_requests_mock.call_count).to_equal(2)
    _assert_sending_requests(signal_requests_mock, 1)


@test
async def send_message_styled_with_attachment(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
    signal_requests_mock_factory: Mocker = Depends(signal_requests_mock_factory_fx),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test send message with attachment."""
    signal_requests_mock = signal_requests_mock_factory()
    with (
        caplog.at_level(
            logging.DEBUG, logger="homeassistant.components.signal_messenger.notify"
        ),
        tempfile.NamedTemporaryFile(
            mode="w", suffix=".png", prefix=os.path.basename(__file__)
        ) as temp_file,
    ):
        temp_file.write("attachment_data")
        data = {"attachments": [temp_file.name], "text_mode": "styled"}
        signal_notification_service.send_message(MESSAGE, data=data)
    post_data = json.loads(signal_requests_mock.request_history[-1].text)
    expect("Sending signal message" in caplog.text).to_be(True)
    expect(signal_requests_mock.called).to_be(True)
    expect(signal_requests_mock.call_count).to_equal(2)
    _assert_sending_requests(signal_requests_mock, 1)
    expect(post_data["text_mode"]).to_equal("styled")


@test
async def send_message_with_attachment_as_url(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
    signal_requests_mock_factory: Mocker = Depends(signal_requests_mock_factory_fx),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test send message with attachment as URL."""
    signal_requests_mock = signal_requests_mock_factory(True, str(len(CONTENT)))
    with caplog.at_level(
        logging.DEBUG, logger="homeassistant.components.signal_messenger.notify"
    ):
        data = {"urls": [URL_ATTACHMENT]}
        signal_notification_service.send_message(MESSAGE, data=data)

    expect("Sending signal message" in caplog.text).to_be(True)
    expect(signal_requests_mock.called).to_be(True)
    expect(signal_requests_mock.call_count).to_equal(3)
    _assert_sending_requests(signal_requests_mock, 1)


@test
async def send_message_styled_with_attachment_as_url(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
    signal_requests_mock_factory: Mocker = Depends(signal_requests_mock_factory_fx),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test send message with attachment as URL."""
    signal_requests_mock = signal_requests_mock_factory(True, str(len(CONTENT)))
    with caplog.at_level(
        logging.DEBUG, logger="homeassistant.components.signal_messenger.notify"
    ):
        data = {"urls": [URL_ATTACHMENT], "text_mode": "styled"}
        signal_notification_service.send_message(MESSAGE, data=data)
    post_data = json.loads(signal_requests_mock.request_history[-1].text)
    expect("Sending signal message" in caplog.text).to_be(True)
    expect(signal_requests_mock.called).to_be(True)
    expect(signal_requests_mock.call_count).to_equal(3)
    _assert_sending_requests(signal_requests_mock, 1)
    expect(post_data["text_mode"]).to_equal("styled")


@test
async def get_attachments(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
    signal_requests_mock_factory: Mocker = Depends(signal_requests_mock_factory_fx),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test getting attachments as URL."""
    signal_requests_mock = signal_requests_mock_factory(True, str(len(CONTENT)))
    data = {"urls": [URL_ATTACHMENT]}
    result = signal_notification_service.get_attachments_as_bytes(
        data, len(CONTENT), hass
    )

    expect(signal_requests_mock.called).to_be(True)
    expect(signal_requests_mock.call_count).to_equal(1)
    expect(result).to_equal([bytearray(CONTENT)])


@test
async def get_attachments_not_on_allowlist(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
    caplog: LogCapture = Depends(caplog_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test getting attachments as URL that aren't on the allowlist."""
    url = "http://dodgyurl.com"
    data = {"urls": [url]}
    with caplog.at_level(
        logging.ERROR, logger="homeassistant.components.signal_messenger.notify"
    ):
        result = signal_notification_service.get_attachments_as_bytes(
            data, len(CONTENT), hass
        )

    expect(f"URL '{url}' not in allow list" in caplog.text).to_be(True)
    expect(result).to_be(None)


@test
async def get_attachments_with_large_attachment(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
    signal_requests_mock_factory: Mocker = Depends(signal_requests_mock_factory_fx),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test getting attachments as URL with large attachment (per Content-Length header) throws error."""
    signal_requests_mock = signal_requests_mock_factory(True, str(len(CONTENT) + 1))
    expect(
        lambda: signal_notification_service.get_attachments_as_bytes(
            {"urls": [URL_ATTACHMENT]}, len(CONTENT), hass
        )
    ).to_raise(ValueError, match="Attachment too large \\(Content-Length reports")

    expect(signal_requests_mock.called).to_be(True)
    expect(signal_requests_mock.call_count).to_equal(1)


@test
async def get_attachments_with_large_attachment_no_header(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
    signal_requests_mock_factory: Mocker = Depends(signal_requests_mock_factory_fx),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test getting attachments as URL with large attachment (per content length) throws error."""
    signal_requests_mock = signal_requests_mock_factory()
    expect(
        lambda: signal_notification_service.get_attachments_as_bytes(
            {"urls": [URL_ATTACHMENT]}, len(CONTENT) - 1, hass
        )
    ).to_raise(ValueError, match="Attachment too large \\(Stream reports")

    expect(signal_requests_mock.called).to_be(True)
    expect(signal_requests_mock.call_count).to_equal(1)


@test
async def get_filenames_with_none_data(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
) -> None:
    """Test getting filenames with None data returns None."""
    data = None
    result = signal_notification_service.get_filenames(data)

    expect(result).to_be(None)


@test
async def get_filenames_with_attachments_data(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
) -> None:
    """Test getting filenames with 'attachments' in data."""
    data = {"attachments": ["test"]}
    result = signal_notification_service.get_filenames(data)

    expect(result).to_equal(["test"])


@test
async def get_filenames_with_multiple_attachments_data(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
) -> None:
    """Test getting filenames with multiple 'attachments' in data."""
    data = {"attachments": ["test", "test2"]}
    result = signal_notification_service.get_filenames(data)

    expect(result).to_equal(["test", "test2"])


@test
async def get_filenames_with_non_list_returns_none(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
) -> None:
    """Test getting filenames with non list data."""
    data = {"attachments": "test"}
    result = signal_notification_service.get_filenames(data)

    expect(result).to_be(None)


@test
async def get_attachments_with_non_list_returns_none(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test getting attachments with non list data."""
    data = {"urls": URL_ATTACHMENT}
    result = signal_notification_service.get_attachments_as_bytes(
        data, len(CONTENT), hass
    )

    expect(result).to_be(None)


@test
async def get_attachments_with_verify_unset(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
    signal_requests_mock_factory: Mocker = Depends(signal_requests_mock_factory_fx),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test getting attachments as URL with verify_ssl unset results in verify=true."""
    signal_requests_mock = signal_requests_mock_factory()
    data = {"urls": [URL_ATTACHMENT]}
    with patch.dict(os.environ, _VERIFY_ENV_CLEAR):
        signal_notification_service.get_attachments_as_bytes(data, len(CONTENT), hass)

    expect(signal_requests_mock.called).to_be(True)
    expect(signal_requests_mock.call_count).to_equal(1)
    expect(signal_requests_mock.last_request.verify).to_be(True)


@test
async def get_attachments_with_verify_set_true(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
    signal_requests_mock_factory: Mocker = Depends(signal_requests_mock_factory_fx),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test getting attachments as URL with verify_ssl set to true results in verify=true."""
    signal_requests_mock = signal_requests_mock_factory()
    data = {"verify_ssl": True, "urls": [URL_ATTACHMENT]}
    with patch.dict(os.environ, _VERIFY_ENV_CLEAR):
        signal_notification_service.get_attachments_as_bytes(data, len(CONTENT), hass)

    expect(signal_requests_mock.called).to_be(True)
    expect(signal_requests_mock.call_count).to_equal(1)
    expect(signal_requests_mock.last_request.verify).to_be(True)


@test
async def get_attachments_with_verify_set_false(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
    signal_requests_mock_factory: Mocker = Depends(signal_requests_mock_factory_fx),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test getting attachments as URL with verify_ssl set to false results in verify=false."""
    signal_requests_mock = signal_requests_mock_factory()
    data = {"verify_ssl": False, "urls": [URL_ATTACHMENT]}
    signal_notification_service.get_attachments_as_bytes(data, len(CONTENT), hass)

    expect(signal_requests_mock.called).to_be(True)
    expect(signal_requests_mock.call_count).to_equal(1)
    expect(signal_requests_mock.last_request.verify).to_be(False)


@test
async def get_attachments_with_verify_set_garbage(
    _trigger: int = Depends(_trigger_executor),
    signal_notification_service: SignalNotificationService = Depends(
        signal_notification_service_fx
    ),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test getting attachments as URL with verify_ssl set to garbage results in None."""
    data = {"verify_ssl": "test", "urls": [URL_ATTACHMENT]}
    result = signal_notification_service.get_attachments_as_bytes(
        data, len(CONTENT), hass
    )

    expect(result).to_be(None)
