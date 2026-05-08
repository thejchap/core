"""Tryke fixtures for the Homeworks integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture


@fixture
def mock_homeworks() -> Generator[MagicMock]:
    """Return a mocked Homeworks client."""
    with (
        patch(
            "homeassistant.components.homeworks.Homeworks", autospec=True
        ) as homeworks_mock,
        patch(
            "homeassistant.components.homeworks.config_flow.Homeworks",
            new=homeworks_mock,
        ),
    ):
        yield homeworks_mock


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.homeworks.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry
