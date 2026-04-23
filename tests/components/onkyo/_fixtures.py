"""Tryke fixtures for Onkyo tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.onkyo.const import DOMAIN

from tests.common import MockConfigEntry

from . import RECEIVER_INFO, RECEIVER_INFO_2, mock_discovery


@fixture
def mock_default_discovery() -> Generator[None]:
    """Mock the discovery functions with default info."""
    with (
        patch.multiple(
            "homeassistant.components.onkyo.receiver",
            DEVICE_INTERVIEW_TIMEOUT=1,
            DEVICE_DISCOVERY_TIMEOUT=1,
        ),
        mock_discovery([RECEIVER_INFO, RECEIVER_INFO_2]),
    ):
        yield


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock integration setup."""
    with patch(
        "homeassistant.components.onkyo.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    data = {"host": RECEIVER_INFO.host}
    options = {
        "volume_resolution": 80,
        "max_volume": 100,
        "input_sources": {"12": "TV", "24": "FM Radio"},
        "listening_modes": {"00": "Stereo", "04": "THX"},
    }
    return MockConfigEntry(
        domain=DOMAIN,
        title=RECEIVER_INFO.model_name,
        unique_id=RECEIVER_INFO.identifier,
        data=data,
        options=options,
    )
