"""The test for the Facebook notify module."""

from http import HTTPStatus

import requests_mock
from tryke import Depends, expect, fixture, test

from homeassistant.components.facebook import notify as fb
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def facebook() -> fb.FacebookNotificationService:
    """Fixture for facebook."""
    access_token = "page-access-token"
    return fb.FacebookNotificationService(access_token)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test
async def send_simple_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    facebook_svc: fb.FacebookNotificationService = Depends(facebook),
) -> None:
    """Test sending a simple message with success."""
    with requests_mock.Mocker() as mock:
        mock.register_uri(requests_mock.POST, fb.BASE_URL, status_code=HTTPStatus.OK)

        message = "This is just a test"
        target = ["+15555551234"]

        facebook_svc.send_message(message=message, target=target)
        expect(mock.called).to_be(True)
        expect(mock.call_count).to_equal(1)

        expected_body = {
            "recipient": {"phone_number": target[0]},
            "message": {"text": message},
            "messaging_type": "MESSAGE_TAG",
            "tag": "HUMAN_AGENT",
        }
        expect(mock.last_request.json()).to_equal(expected_body)

        expected_params = {"access_token": ["page-access-token"]}
        expect(mock.last_request.qs).to_equal(expected_params)


@test
async def send_multiple_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    facebook_svc: fb.FacebookNotificationService = Depends(facebook),
) -> None:
    """Test sending a message to multiple targets."""
    with requests_mock.Mocker() as mock:
        mock.register_uri(requests_mock.POST, fb.BASE_URL, status_code=HTTPStatus.OK)

        message = "This is just a test"
        targets = ["+15555551234", "+15555551235"]

        facebook_svc.send_message(message=message, target=targets)
        expect(mock.called).to_be(True)
        expect(mock.call_count).to_equal(2)

        for idx, target in enumerate(targets):
            request = mock.request_history[idx]
            expected_body = {
                "recipient": {"phone_number": target},
                "message": {"text": message},
                "messaging_type": "MESSAGE_TAG",
                "tag": "HUMAN_AGENT",
            }
            expect(request.json()).to_equal(expected_body)

            expected_params = {"access_token": ["page-access-token"]}
            expect(request.qs).to_equal(expected_params)


@test
async def send_message_attachment(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    facebook_svc: fb.FacebookNotificationService = Depends(facebook),
) -> None:
    """Test sending a message with a remote attachment."""
    with requests_mock.Mocker() as mock:
        mock.register_uri(requests_mock.POST, fb.BASE_URL, status_code=HTTPStatus.OK)

        message = "This will be thrown away."
        data = {
            "attachment": {
                "type": "image",
                "payload": {"url": "http://www.example.com/image.jpg"},
            }
        }
        target = ["+15555551234"]

        facebook_svc.send_message(message=message, data=data, target=target)
        expect(mock.called).to_be(True)
        expect(mock.call_count).to_equal(1)

        expected_body = {
            "recipient": {"phone_number": target[0]},
            "message": data,
            "messaging_type": "MESSAGE_TAG",
            "tag": "HUMAN_AGENT",
        }
        expect(mock.last_request.json()).to_equal(expected_body)

        expected_params = {"access_token": ["page-access-token"]}
        expect(mock.last_request.qs).to_equal(expected_params)


@test
async def send_targetless_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    facebook_svc: fb.FacebookNotificationService = Depends(facebook),
) -> None:
    """Test sending a message without a target."""
    with requests_mock.Mocker() as mock:
        mock.register_uri(requests_mock.POST, fb.BASE_URL, status_code=HTTPStatus.OK)

        facebook_svc.send_message(message="going nowhere")
        expect(mock.called).to_be(False)


@test
async def send_message_with_400(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    facebook_svc: fb.FacebookNotificationService = Depends(facebook),
) -> None:
    """Test sending a message with a 400 from Facebook."""
    with requests_mock.Mocker() as mock:
        mock.register_uri(
            requests_mock.POST,
            fb.BASE_URL,
            status_code=HTTPStatus.BAD_REQUEST,
            json={
                "error": {
                    "message": "Invalid OAuth access token.",
                    "type": "OAuthException",
                    "code": 190,
                    "fbtrace_id": "G4Da2pFp2Dp",
                }
            },
        )
        facebook_svc.send_message(message="nope!", target=["+15555551234"])
        expect(mock.called).to_be(True)
        expect(mock.call_count).to_equal(1)
