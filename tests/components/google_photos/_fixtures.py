"""Tryke fixtures for the Google Photos integration."""

from collections.abc import AsyncGenerator, Awaitable, Callable, Generator
import time
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from google_photos_library_api.api import GooglePhotosLibraryApi
from google_photos_library_api.model import (
    Album,
    ListAlbumResult,
    ListMediaItemResult,
    MediaItem,
    UserInfoResult,
)
from tryke import Depends, fixture

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.google_photos.const import DOMAIN, OAUTH2_SCOPES
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
    async_load_json_array_fixture,
    async_load_json_object_fixture,
)
from tests.hass_fixtures import hass as hass_fx

USER_IDENTIFIER = "user-identifier-1"
CONFIG_ENTRY_ID = "user-identifier-1"
CLIENT_ID = "1234"
CLIENT_SECRET = "5678"
FAKE_ACCESS_TOKEN = "some-access-token"
FAKE_REFRESH_TOKEN = "some-refresh-token"
EXPIRES_IN = 3600


@fixture
def expires_at() -> int:
    """Set the OAuth token expiration time."""
    return int(time.time() + EXPIRES_IN)


@fixture
def scopes() -> list[str]:
    """Return scopes used during the config entry."""
    return OAUTH2_SCOPES


@fixture
def token_entry(
    expires_at: int = Depends(expires_at),
    scopes: list[str] = Depends(scopes),
) -> dict[str, Any]:
    """Provide OAuth 'token' data for a ConfigEntry."""
    return {
        "access_token": FAKE_ACCESS_TOKEN,
        "refresh_token": FAKE_REFRESH_TOKEN,
        "scope": " ".join(scopes),
        "type": "Bearer",
        "expires_at": expires_at,
        "expires_in": EXPIRES_IN,
    }


@fixture
def config_entry(
    token_entry: dict[str, Any] = Depends(token_entry),
) -> MockConfigEntry:
    """Provide a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=CONFIG_ENTRY_ID,
        data={
            "auth_implementation": DOMAIN,
            "token": token_entry,
        },
        title="Account Name",
    )


@fixture
async def setup_credentials(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Set up credentials."""
    await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
    )


@fixture
def fixture_name() -> str | None:
    """Provide a json fixture file name."""
    return None


@fixture
def user_identifier() -> str:
    """Provide user identifier."""
    return USER_IDENTIFIER


@fixture
def api_error() -> Exception | None:
    """Provide an api error to inject."""
    return None


@fixture
async def mock_api(
    hass: HomeAssistant = Depends(hass_fx),
    fixture_name: str | None = Depends(fixture_name),
    user_identifier: str = Depends(user_identifier),
    api_error: Exception | None = Depends(api_error),
) -> Mock:
    """Set up fake Google Photos API responses."""
    mock_api = AsyncMock(GooglePhotosLibraryApi, autospec=True)
    mock_api.get_user_info.return_value = UserInfoResult(
        id=user_identifier,
        name="Test Name",
    )

    responses = (
        await async_load_json_array_fixture(hass, fixture_name, DOMAIN)
        if fixture_name
        else []
    )

    async def list_media_items(*args: Any) -> AsyncGenerator[ListMediaItemResult]:
        for response in responses:
            mock_list_media_items = Mock(ListMediaItemResult)
            mock_list_media_items.media_items = [
                MediaItem.from_dict(media_item) for media_item in response["mediaItems"]
            ]
            yield mock_list_media_items

    mock_api.list_media_items.return_value.__aiter__ = list_media_items
    mock_api.list_media_items.return_value.__anext__ = list_media_items
    mock_api.list_media_items.side_effect = api_error

    async def get_media_item(media_item_id: str, **kwargs: Any) -> Mock:
        for response in responses:
            for media_item in response["mediaItems"]:
                if media_item["id"] == media_item_id:
                    return MediaItem.from_dict(media_item)
        return None

    mock_api.get_media_item = get_media_item

    async def list_albums(*args: Any, **kwargs: Any) -> AsyncGenerator[ListAlbumResult]:
        album_list = await async_load_json_object_fixture(
            hass, "list_albums.json", DOMAIN
        )
        mock_list_album_result = Mock(ListAlbumResult)
        mock_list_album_result.albums = [
            Album.from_dict(album) for album in album_list["albums"]
        ]
        yield mock_list_album_result

    mock_api.list_albums.return_value.__aiter__ = list_albums
    mock_api.list_albums.return_value.__anext__ = list_albums
    mock_api.list_albums.side_effect = api_error

    async def get_album(album_id: str, **kwargs: Any) -> Mock:
        album_list = await async_load_json_object_fixture(
            hass, "list_albums.json", DOMAIN
        )
        for album in album_list["albums"]:
            if album["id"] == album_id:
                return Album.from_dict(album)
        return None

    mock_api.get_album = get_album
    mock_api.get_album.side_effect = api_error

    return mock_api


@fixture
def mock_setup() -> Generator[Mock]:
    """Fixture to mock out integration setup."""
    with patch(
        "homeassistant.components.google_photos.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_patch_api(mock_api: Mock = Depends(mock_api)) -> Generator[None]:
    """Patch the config flow api."""
    with patch(
        "homeassistant.components.google_photos.config_flow.GooglePhotosLibraryApi",
        return_value=mock_api,
    ):
        yield


@fixture
def updated_token_entry() -> dict[str, Any]:
    """Provide test-specific overrides to token data from oauth token endpoint."""
    return {}
