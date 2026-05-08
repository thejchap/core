"""Tryke fixtures for the neato integration."""

from __future__ import annotations

from tryke import Depends, fixture

from homeassistant.components.neato.const import DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_application_credentials

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"


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
        domain=DOMAIN,
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "refresh_token": "mock-refresh-token",
                "access_token": "mock-access-token",
                "type": "Bearer",
                "expires_in": 60,
            },
        },
    )
