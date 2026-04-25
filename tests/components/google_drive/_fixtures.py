"""Tryke fixtures for the Google Drive integration."""

from collections.abc import Generator
import time
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.google_drive.const import DOMAIN
from homeassistant.const import UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util.unit_conversion import InformationConverter

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"
HA_UUID = "0a123c"
TEST_USER_EMAIL = "testuser@domain.com"
CONFIG_ENTRY_TITLE = "Google Drive entry title"


@fixture
async def setup_credentials(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Set up application credentials."""
    await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
    )


@fixture
def mock_api() -> Generator[MagicMock]:
    """Return a mocked GoogleDriveApi."""
    with patch(
        "homeassistant.components.google_drive.api.GoogleDriveApi"
    ) as mock_api_cl:
        api_mock = mock_api_cl.return_value

        def mock_get_user(params=None):
            params = params or {}
            fields = params.get("fields")
            result = {}
            if not fields or "storageQuota" in fields:
                result["storageQuota"] = {
                    "limit": InformationConverter.convert(
                        10, UnitOfInformation.GIBIBYTES, UnitOfInformation.BYTES
                    ),
                    "usage": InformationConverter.convert(
                        5, UnitOfInformation.GIBIBYTES, UnitOfInformation.BYTES
                    ),
                    "usageInDrive": InformationConverter.convert(
                        2, UnitOfInformation.GIBIBYTES, UnitOfInformation.BYTES
                    ),
                    "usageInTrash": InformationConverter.convert(
                        1, UnitOfInformation.GIBIBYTES, UnitOfInformation.BYTES
                    ),
                }
            if not fields or "user(emailAddress)" in fields:
                result["user"] = {"emailAddress": TEST_USER_EMAIL}
            return result

        api_mock.get_user = AsyncMock(side_effect=mock_get_user)
        api_mock.list_files = AsyncMock(
            side_effect=[
                {"files": [{"id": "HA folder ID", "name": "HA folder name"}]},
                {"files": []},
            ]
        )
        yield api_mock


@fixture
def mock_instance_id() -> Generator[None]:
    """Mock instance_id."""
    with patch(
        "homeassistant.components.google_drive.config_flow.instance_id.async_get",
        return_value=HA_UUID,
    ):
        yield


@fixture
def expires_at() -> int:
    """Set the OAuth token expiration time."""
    return time.time() + 3600


@fixture
def config_entry(expires_at: int = Depends(expires_at)) -> MockConfigEntry:
    """Return a MockConfigEntry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_USER_EMAIL,
        title=CONFIG_ENTRY_TITLE,
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "mock-access-token",
                "refresh_token": "mock-refresh-token",
                "expires_at": expires_at,
                "scope": "https://www.googleapis.com/auth/drive.file",
            },
        },
    )
