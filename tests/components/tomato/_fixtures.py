"""Tryke fixtures for the Tomato device tracker tests."""

from collections.abc import Generator
from unittest import mock

from tryke import fixture


@fixture
def mock_exception_logger() -> Generator[mock.MagicMock]:
    """Mock the tomato device tracker exception logger."""
    with mock.patch(
        "homeassistant.components.tomato.device_tracker._LOGGER.exception"
    ) as mock_exception_logger:
        yield mock_exception_logger


@fixture
def mock_session_send() -> Generator[mock.MagicMock]:
    """Mock requests.Session().send."""
    with mock.patch("requests.Session.send") as mock_session_send:
        yield mock_session_send
