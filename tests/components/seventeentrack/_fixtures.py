"""Tryke fixtures for 17Track tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.seventeentrack.const import (
    CONF_SHOW_ARCHIVED,
    CONF_SHOW_DELIVERED,
    DEFAULT_SHOW_ARCHIVED,
    DEFAULT_SHOW_DELIVERED,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry

DEFAULT_SUMMARY = {
    "Not Found": 0,
    "In Transit": 0,
    "Expired": 0,
    "Ready to be Picked Up": 0,
    "Undelivered": 0,
    "Delivered": 0,
    "Returned": 0,
}

ACCOUNT_ID = "1234"

VALID_CONFIG = {
    CONF_USERNAME: "test",
    CONF_PASSWORD: "test",
}

VALID_OPTIONS = {
    CONF_SHOW_ARCHIVED: True,
    CONF_SHOW_DELIVERED: True,
}


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.seventeentrack.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain="seventeentrack",
        data=VALID_CONFIG,
        options=VALID_OPTIONS,
        unique_id=ACCOUNT_ID,
    )


@fixture
def mock_config_entry_with_default_options() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain="seventeentrack",
        data=VALID_CONFIG,
        options={
            CONF_SHOW_ARCHIVED: DEFAULT_SHOW_ARCHIVED,
            CONF_SHOW_DELIVERED: DEFAULT_SHOW_DELIVERED,
        },
        unique_id=ACCOUNT_ID,
    )


@fixture
def mock_seventeentrack() -> Generator[AsyncMock]:
    """Build a fixture for the 17Track API."""
    mock_seventeentrack_api = AsyncMock()
    with (
        patch(
            "homeassistant.components.seventeentrack.SeventeenTrackClient",
            return_value=mock_seventeentrack_api,
        ),
        patch(
            "homeassistant.components.seventeentrack.config_flow.SeventeenTrackClient",
            return_value=mock_seventeentrack_api,
        ) as mock_seventeentrack_api,
    ):
        mock_seventeentrack_api.return_value.profile.account_id = ACCOUNT_ID
        mock_seventeentrack_api.return_value.profile.login.return_value = True
        mock_seventeentrack_api.return_value.profile.packages.return_value = []
        mock_seventeentrack_api.return_value.profile.summary.return_value = (
            DEFAULT_SUMMARY
        )
        yield mock_seventeentrack_api
