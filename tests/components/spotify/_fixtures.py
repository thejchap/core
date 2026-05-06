"""Tryke fixtures for the Spotify integration."""

from collections.abc import Generator
import time
from unittest.mock import AsyncMock, patch

from spotifyaio.models import (
    Album,
    Artist,
    Devices,
    FollowedArtistResponse,
    NewReleasesResponseInner,
    PlaybackState,
    PlayedTrackResponse,
    Playlist,
    PlaylistResponse,
    SavedAlbumResponse,
    SavedShowResponse,
    SavedTrackResponse,
    Show,
    ShowEpisodesResponse,
    TopArtistsResponse,
    TopTracksResponse,
    UserProfile,
)
from tryke import Depends, fixture

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.spotify.const import DOMAIN, SPOTIFY_SCOPES
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry, load_fixture
from tests.hass_fixtures import hass as hass_fx

SCOPES = " ".join(SPOTIFY_SCOPES)


@fixture
def expires_at() -> int:
    """Set the OAuth token expiration time."""
    return time.time() + 3600


@fixture
def mock_config_entry(expires_at: int = Depends(expires_at)) -> MockConfigEntry:
    """Create Spotify entry in Home Assistant."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="spotify_1",
        unique_id="1112264111",
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "mock-access-token",
                "refresh_token": "mock-refresh-token",
                "expires_at": expires_at,
                "scope": SCOPES,
            },
            "id": "1112264111",
            "name": "spotify_account_1",
        },
        entry_id="01J5TX5A0FF6G5V0QJX6HBC94T",
    )


@fixture
async def setup_credentials(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Set up credentials."""
    await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential("CLIENT_ID", "CLIENT_SECRET"),
        DOMAIN,
    )


@fixture
def patch_sleep() -> Generator[None]:
    """Patch out the after-request sleep used by media_player."""
    with patch("homeassistant.components.spotify.media_player.AFTER_REQUEST_SLEEP", 0):
        yield


@fixture
def mock_spotify() -> Generator[AsyncMock]:
    """Mock the Spotify API."""
    with (
        patch(
            "homeassistant.components.spotify.SpotifyClient", autospec=True
        ) as spotify_mock,
        patch(
            "homeassistant.components.spotify.config_flow.SpotifyClient",
            new=spotify_mock,
        ),
    ):
        client = spotify_mock.return_value
        for fixture_name, method, obj in (
            (
                "current_user_playlist.json",
                "get_playlists_for_current_user",
                PlaylistResponse,
            ),
            ("saved_albums.json", "get_saved_albums", SavedAlbumResponse),
            ("saved_tracks.json", "get_saved_tracks", SavedTrackResponse),
            ("saved_shows.json", "get_saved_shows", SavedShowResponse),
            (
                "recently_played_tracks.json",
                "get_recently_played_tracks",
                PlayedTrackResponse,
            ),
            ("top_artists.json", "get_top_artists", TopArtistsResponse),
            ("top_tracks.json", "get_top_tracks", TopTracksResponse),
            ("show_episodes.json", "get_show_episodes", ShowEpisodesResponse),
            ("artist_albums.json", "get_artist_albums", NewReleasesResponseInner),
        ):
            getattr(client, method).return_value = obj.from_json(
                load_fixture(fixture_name, DOMAIN)
            ).items
        for fixture_name, method, obj in (
            (
                "playback.json",
                "get_playback",
                PlaybackState,
            ),
            ("current_user.json", "get_current_user", UserProfile),
            ("playlist.json", "get_playlist", Playlist),
            ("album.json", "get_album", Album),
            ("artist.json", "get_artist", Artist),
            ("show.json", "get_show", Show),
        ):
            getattr(client, method).return_value = obj.from_json(
                load_fixture(fixture_name, DOMAIN)
            )
        client.get_followed_artists.return_value = FollowedArtistResponse.from_json(
            load_fixture("followed_artists.json", DOMAIN)
        ).artists.items
        client.get_devices.return_value = Devices.from_json(
            load_fixture("devices.json", DOMAIN)
        ).devices
        yield spotify_mock
