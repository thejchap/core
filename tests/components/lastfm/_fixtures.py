"""Tryke fixtures for the LastFM integration."""

from collections.abc import Awaitable, Callable
from unittest.mock import patch

from pylast import Track, WSError
from tryke import Depends, fixture

from homeassistant.components.lastfm.const import CONF_MAIN_USER, CONF_USERS, DOMAIN
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import API_KEY, USERNAME_1, USERNAME_2, MockNetwork, MockUser

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

type ComponentSetup = Callable[[MockConfigEntry, MockUser], Awaitable[None]]


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
    """Create LastFM imported entry in Home Assistant."""
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
def setup_integration(
    hass: HomeAssistant = Depends(hass_fixture),
) -> ComponentSetup:
    """Fixture for setting up the component."""

    async def func(mock_config_entry: MockConfigEntry, mock_user: MockUser) -> None:
        mock_config_entry.add_to_hass(hass)
        with patch("pylast.User", return_value=mock_user):
            assert await async_setup_component(hass, DOMAIN, {})
            await hass.async_block_till_done()

    return func


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


@fixture
def first_time_user() -> MockUser:
    """Return first time mock user."""
    return MockUser(now_playing_result=None, top_tracks=[], recent_tracks=[])


@fixture
def not_found_user() -> MockUser:
    """Return not found mock user."""
    return MockUser(thrown_error=WSError("network", "status", "User not found"))
