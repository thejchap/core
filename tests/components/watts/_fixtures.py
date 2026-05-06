"""Tryke fixtures for the Watts integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.watts.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx

CLIENT_ID = "test_client_id"
CLIENT_SECRET = "test_client_secret"
TEST_USER_ID = "test-user-id"
TEST_ACCESS_TOKEN = "test-access-token"
TEST_REFRESH_TOKEN = "test-refresh-token"
TEST_ID_TOKEN = "test-id-token"
TEST_PROFILE_INFO = "test-profile-info"
TEST_EXPIRES_AT = 9999999999


@fixture
async def setup_credentials(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Ensure the application credentials are registered for each test."""
    await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET, name="Watts"),
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.watts.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Watts Vision",
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": TEST_ACCESS_TOKEN,
                "refresh_token": TEST_REFRESH_TOKEN,
                "id_token": TEST_ID_TOKEN,
                "profile_info": TEST_PROFILE_INFO,
                "expires_at": TEST_EXPIRES_AT,
            },
        },
        entry_id="01J0BC4QM2YBRP6H5G933CETI8",
        unique_id=TEST_USER_ID,
    )


@fixture
def skip_cloud() -> Generator[None]:
    """Skip setting up cloud."""
    with patch("homeassistant.components.cloud.async_setup", return_value=True):
        yield
