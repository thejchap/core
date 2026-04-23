"""Tryke fixtures for LastFM tests."""

from __future__ import annotations

from pylast import Track
from tryke import fixture

from homeassistant.components.lastfm.const import CONF_MAIN_USER, CONF_USERS, DOMAIN
from homeassistant.const import CONF_API_KEY

from . import API_KEY, USERNAME_1, USERNAME_2, MockNetwork, MockUser

from tests.common import MockConfigEntry


@fixture
def config_entry() -> MockConfigEntry:
    """Create LastFM entry in Home Assistant."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_API_KEY: API_KEY,
            CONF_MAIN_USER: USERNAME_1,
            CONF_USERS: [USERNAME_1, USERNAME_2],
        },
    )


@fixture
def imported_config_entry() -> MockConfigEntry:
    """Create LastFM entry from import."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_API_KEY: API_KEY,
            CONF_MAIN_USER: None,
            CONF_USERS: [USERNAME_1, USERNAME_2],
        },
    )


@fixture
def default_user() -> MockUser:
    """Return default mock user."""
    return MockUser(
        now_playing_result=Track("artist", "title", MockNetwork("lastfm")),
        top_tracks=[Track("artist", "title", MockNetwork("lastfm"))],
        recent_tracks=[Track("artist", "title", MockNetwork("lastfm"))],
        friends=[MockUser()],
    )


@fixture
def default_user_no_friends() -> MockUser:
    """Return default mock user without friends."""
    return MockUser(
        now_playing_result=Track("artist", "title", MockNetwork("lastfm")),
        top_tracks=[Track("artist", "title", MockNetwork("lastfm"))],
        recent_tracks=[Track("artist", "title", MockNetwork("lastfm"))],
    )
