"""Tryke fixtures for the denonavr integration."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture

TEST_NAME = "Test_Receiver"
TEST_MODEL = "model5"
TEST_RECEIVER_TYPE = "avr-x"
TEST_SERIALNUMBER = "123456789"
TEST_MANUFACTURER = "Denon"


@fixture
def denonavr_connect() -> Generator[None]:
    """Mock denonavr connection and entry setup."""
    with (
        patch(
            "homeassistant.components.denonavr.receiver.DenonAVR.async_setup",
            return_value=None,
        ),
        patch(
            "homeassistant.components.denonavr.receiver.DenonAVR.async_update",
            return_value=None,
        ),
        patch(
            "homeassistant.components.denonavr.receiver.DenonAVR.support_sound_mode",
            return_value=True,
        ),
        patch(
            "homeassistant.components.denonavr.receiver.DenonAVR.name",
            TEST_NAME,
        ),
        patch(
            "homeassistant.components.denonavr.receiver.DenonAVR.model_name",
            TEST_MODEL,
        ),
        patch(
            "homeassistant.components.denonavr.receiver.DenonAVR.serial_number",
            TEST_SERIALNUMBER,
        ),
        patch(
            "homeassistant.components.denonavr.receiver.DenonAVR.manufacturer",
            TEST_MANUFACTURER,
        ),
        patch(
            "homeassistant.components.denonavr.receiver.DenonAVR.receiver_type",
            TEST_RECEIVER_TYPE,
        ),
        patch(
            "homeassistant.components.denonavr.async_setup_entry",
            return_value=True,
        ),
    ):
        yield
