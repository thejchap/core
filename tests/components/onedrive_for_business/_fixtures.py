"""Tryke fixtures for the onedrive_for_business integration."""

from __future__ import annotations

import time

from tryke import Depends, fixture

from homeassistant.components.onedrive_for_business.const import (
    CONF_FOLDER_ID,
    CONF_FOLDER_PATH,
    CONF_TENANT_ID,
    DOMAIN,
    OAUTH_SCOPES,
)
from homeassistant.core import HomeAssistant

from .const import CLIENT_ID, CLIENT_SECRET, TENANT_ID

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_application_credentials


@fixture
async def setup_credentials(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up the OAuth2 application_credentials chain."""
    await setup_application_credentials(hass, DOMAIN, CLIENT_ID, CLIENT_SECRET)


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="John Doe's OneDrive",
        domain=DOMAIN,
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "mock-access-token",
                "refresh_token": "mock-refresh-token",
                "expires_at": time.time() + 3600,
                "scope": " ".join(OAUTH_SCOPES),
            },
            CONF_FOLDER_PATH: "backups/home_assistant",
            CONF_FOLDER_ID: "my_folder_id",
            CONF_TENANT_ID: TENANT_ID,
        },
        unique_id="mock_drive_id",
    )
