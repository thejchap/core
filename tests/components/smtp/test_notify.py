"""The tests for the notify smtp platform."""

from pathlib import Path
import re
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config as hass_config
from homeassistant.components import notify
from homeassistant.components.smtp.const import DOMAIN
from homeassistant.const import SERVICE_RELOAD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.setup import async_setup_component

from tests.common import get_fixture_path
from tests.components.smtp._fixtures import MockSMTP, message
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def reload_notify(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Verify we can reload the notify service."""

    with patch(
        "homeassistant.components.smtp.notify.MailNotificationService.connection_is_valid"
    ):
        expect(
            await async_setup_component(
                hass,
                notify.DOMAIN,
                {
                    notify.DOMAIN: [
                        {
                            "name": DOMAIN,
                            "platform": DOMAIN,
                            "recipient": "test@example.com",
                            "sender": "test@example.com",
                        },
                    ]
                },
            )
        ).to_be(True)
        await hass.async_block_till_done()

    expect(hass.services.has_service(notify.DOMAIN, DOMAIN)).to_be(True)

    yaml_path = get_fixture_path("configuration.yaml", "smtp")
    with (
        patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path),
        patch(
            "homeassistant.components.smtp.notify.MailNotificationService.connection_is_valid"
        ),
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    expect(hass.services.has_service(notify.DOMAIN, DOMAIN)).to_be(False)
    expect(hass.services.has_service(notify.DOMAIN, "smtp_reloaded")).to_be(True)


HTML = """
        <!DOCTYPE html>
        <html lang="en" xmlns="http://www.w3.org/1999/xhtml">
            <head><meta charset="UTF-8"></head>
            <body>
              <div>
                <h1>Intruder alert at apartment!!</h1>
              </div>
              <div>
                <img alt="tests/testing_config/notify/test.jpg" src="cid:tests/testing_config/notify/test.jpg"/>
              </div>
            </body>
        </html>"""


@test.cases(
    test.case(
        "text_and_images",
        message_data="Test msg",
        data={"images": ["tests/testing_config/notify/test.jpg"]},
        content_type="Content-Type: multipart/mixed",
    ),
    test.case(
        "text_html_and_images",
        message_data="Test msg",
        data={"html": HTML, "images": ["tests/testing_config/notify/test.jpg"]},
        content_type="Content-Type: multipart/related",
    ),
    test.case(
        "image_does_not_exist",
        message_data="Test msg",
        data={
            "html": HTML,
            "images": ["tests/testing_config/notify/test_not_exists.jpg"],
        },
        content_type="Content-Type: multipart/related",
    ),
    test.case(
        "image_wrong_type",
        message_data="Test msg",
        data={"html": HTML, "images": ["tests/testing_config/notify/test.pdf"]},
        content_type="Content-Type: multipart/related",
    ),
)
async def send_message(
    *,
    message_data: str,
    data: dict,
    content_type: str,
    hass: HomeAssistant = Depends(_trigger_executor),
    message: MockSMTP = Depends(message),
) -> None:
    """Verify if we can send messages of all types correctly."""
    sample_email = "<mock@mock>"
    message.hass = hass
    hass.config.allowlist_external_dirs.add(Path("tests/testing_config").resolve())
    with patch("email.utils.make_msgid", return_value=sample_email):
        result, _ = message.send_message(message_data, data=data)
        expect(content_type in result).to_be(True)


@test
async def sending_insecure_files_fails(
    hass: HomeAssistant = Depends(_trigger_executor),
    message: MockSMTP = Depends(message),
) -> None:
    """Verify if we cannot send messages with insecure attachments."""
    message_data = "Test msg"
    data = {"images": ["tests/testing_config/notify/test.jpg"]}
    sample_email = "<mock@mock>"
    message.hass = hass
    exc: ServiceValidationError | None = None
    with patch("email.utils.make_msgid", return_value=sample_email):
        try:
            message.send_message(message_data, data=data)
        except ServiceValidationError as err:
            exc = err
    expect(exc is not None).to_be(True)
    expect(exc.translation_key).to_equal("remote_path_not_allowed")
    expect(exc.translation_domain).to_equal(DOMAIN)
    expect(str(exc.translation_placeholders["file_path"])).to_equal(
        "tests/testing_config/notify"
    )
    expect(bool(exc.translation_placeholders["url"])).to_be(True)
    expect(exc.translation_placeholders["file_name"]).to_equal("test.jpg")


@test
async def send_text_message(
    hass: HomeAssistant = Depends(_trigger_executor),
    message: MockSMTP = Depends(message),
) -> None:
    """Verify if we can send simple text message."""
    expected = (
        '^Content-Type: text/plain; charset="us-ascii"\n'
        "MIME-Version: 1.0\n"
        "Content-Transfer-Encoding: 7bit\n"
        "Subject: Home Assistant\n"
        "To: recip1@example.com,testrecip@test.com\n"
        "From: Home Assistant <test@test.com>\n"
        "X-Mailer: Home Assistant\n"
        "Date: [^\n]+\n"
        "Message-Id: <[^@]+@[^>]+>\n"
        "\n"
        "Test msg$"
    )
    sample_email = "<mock@mock>"
    message_data = "Test msg"
    with patch("email.utils.make_msgid", return_value=sample_email):
        result, _ = message.send_message(message_data)
        expect(re.search(expected, result) is not None).to_be(True)


@test.cases(
    test.case("default_recipient", target=None),
    test.case("override_recipient", target="target@example.com"),
)
async def send_target_message(
    *,
    target: str | None,
    hass: HomeAssistant = Depends(_trigger_executor),
    message: MockSMTP = Depends(message),
) -> None:
    """Verify if we can send email to correct recipient."""
    sample_email = "<mock@mock>"
    message_data = "Test msg"
    with patch("email.utils.make_msgid", return_value=sample_email):
        if not target:
            expected_recipient = ["recip1@example.com", "testrecip@test.com"]
        else:
            expected_recipient = target

        _, recipient = message.send_message(message_data, target=target)
        expect(recipient).to_equal(expected_recipient)
