"""Tryke fixtures for the Dropbox integration."""

from collections.abc import Generator
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture

from homeassistant.components.application_credentials import (
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.dropbox.const import DOMAIN, OAUTH2_SCOPES
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"
ACCOUNT_ID = "dbid:1234567890abcdef"
ACCOUNT_EMAIL = "user@example.com"
CONFIG_ENTRY_TITLE = "Dropbox test account"


@fixture
async def setup_credentials(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Set up application credentials for Dropbox."""
    await async_setup_component(hass, "application_credentials", {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
    )


@fixture
def account_info() -> SimpleNamespace:
    """Return mocked Dropbox account information."""
    return SimpleNamespace(account_id=ACCOUNT_ID, email=ACCOUNT_EMAIL)


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a default Dropbox config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=ACCOUNT_ID,
        title=CONFIG_ENTRY_TITLE,
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "mock-access-token",
                "refresh_token": "mock-refresh-token",
                "expires_at": 9_999_999_999,
                "scope": " ".join(OAUTH2_SCOPES),
            },
        },
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.dropbox.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_dropbox_client(
    account_info: SimpleNamespace = Depends(account_info),
) -> Generator[MagicMock]:
    """Patch DropboxAPIClient to exercise auth while mocking API calls."""
    client = MagicMock()
    client.list_folder = AsyncMock(return_value=[])
    client.download_file = MagicMock()
    client.upload_file = AsyncMock()
    client.delete_file = AsyncMock()

    captured_auth: list[object] = []

    def capture_auth(auth: object) -> MagicMock:
        captured_auth.append(auth)
        return client

    async def get_account_info_with_auth() -> object:
        await captured_auth[-1].async_get_access_token()
        return client.get_account_info.return_value

    client.get_account_info = AsyncMock(
        side_effect=get_account_info_with_auth,
        return_value=account_info,
    )

    with (
        patch(
            "homeassistant.components.dropbox.config_flow.DropboxAPIClient",
            side_effect=capture_auth,
        ),
        patch(
            "homeassistant.components.dropbox.DropboxAPIClient",
            side_effect=capture_auth,
        ),
    ):
        yield client
