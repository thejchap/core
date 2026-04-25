"""Tryke fixtures for MJPEG IP Camera integration tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from requests_mock import Mocker
from tryke import fixture

from homeassistant.components.mjpeg.const import (
    CONF_MJPEG_URL,
    CONF_STILL_IMAGE_URL,
    DOMAIN,
)
from homeassistant.const import (
    CONF_AUTHENTICATION,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    HTTP_BASIC_AUTHENTICATION,
)

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="My MJPEG Camera",
        domain=DOMAIN,
        data={},
        options={
            CONF_AUTHENTICATION: HTTP_BASIC_AUTHENTICATION,
            CONF_MJPEG_URL: "https://example.com/mjpeg",
            CONF_PASSWORD: "supersecret",
            CONF_STILL_IMAGE_URL: "http://example.com/still",
            CONF_USERNAME: "frenck",
            CONF_VERIFY_SSL: True,
        },
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.mjpeg.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_mjpeg_requests() -> Generator[Mocker]:
    """Provide a requests_mock mocker for MJPEG requests."""
    with Mocker() as mocker:
        mocker.get("https://example.com/mjpeg", text="resp")
        mocker.get("https://example.com/still", text="resp")
        yield mocker
