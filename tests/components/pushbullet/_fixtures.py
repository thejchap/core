"""Tryke fixtures for pushbullet tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

from pushbullet import PushBullet
from requests_mock import Mocker
from tryke import fixture

from tests.common import load_fixture


@fixture
def requests_mock_fixture() -> Generator[Mocker]:
    """Provide a requests mocker seeded with pushbullet responses."""
    with Mocker() as mock:
        mock.get(
            PushBullet.DEVICES_URL,
            text=load_fixture("devices.json", "pushbullet"),
        )
        mock.get(
            PushBullet.ME_URL,
            text=load_fixture("user_info.json", "pushbullet"),
        )
        mock.get(
            PushBullet.CHATS_URL,
            text=load_fixture("chats.json", "pushbullet"),
        )
        mock.get(
            PushBullet.CHANNELS_URL,
            text=load_fixture("channels.json", "pushbullet"),
        )
        yield mock


@fixture
def mock_setup_entry() -> Generator[None]:
    """Patch pushbullet setup entry."""
    with patch(
        "homeassistant.components.pushbullet.async_setup_entry", return_value=True
    ):
        yield
