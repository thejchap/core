"""Tryke fixtures for SwitchBot Cloud tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture

from homeassistant.components.switchbot_cloud import SwitchBotAPI


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.switchbot_cloud.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock


@fixture
def mock_list_devices() -> Generator[MagicMock]:
    """Mock list_devices."""
    with patch.object(SwitchBotAPI, "list_devices") as mock:
        yield mock


@fixture
def mock_get_status() -> Generator[MagicMock]:
    """Mock get_status."""
    with patch.object(SwitchBotAPI, "get_status") as mock:
        yield mock


@fixture
def mock_setup_webhook() -> Generator[MagicMock]:
    """Mock setup_webhook."""
    with patch.object(SwitchBotAPI, "setup_webhook") as mock:
        yield mock


@fixture
def mock_delete_webhook() -> Generator[MagicMock]:
    """Mock delete_webhook."""
    with patch.object(SwitchBotAPI, "delete_webhook") as mock:
        yield mock


@fixture
def mock_get_webook_configuration() -> Generator[MagicMock]:
    """Mock get_webook_configuration."""
    with patch.object(SwitchBotAPI, "get_webook_configuration") as mock:
        yield mock


@fixture
def mock_after_command_refresh() -> Generator[None]:
    """Mock after command refresh constants (autouse equivalent)."""
    with (
        patch(
            "homeassistant.components.switchbot_cloud.const.AFTER_COMMAND_REFRESH",
            0,
        ),
        patch(
            "homeassistant.components.switchbot_cloud.const.COVER_ENTITY_AFTER_COMMAND_REFRESH",
            0,
        ),
    ):
        yield
