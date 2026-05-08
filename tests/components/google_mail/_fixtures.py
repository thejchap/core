"""Tryke fixtures for the Google Mail integration."""

from collections.abc import Generator
import time

from tryke import Depends, fixture

from homeassistant.components.google_mail.const import DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import aioclient_mock, hass as hass_fixture
from tests.hass_tryke_helpers import setup_application_credentials
from tests.test_util.aiohttp import AiohttpClientMocker

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.settings.basic",
]
TITLE = "example@gmail.com"


@fixture
async def setup_credentials(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up application credentials for OAuth2."""
    await setup_application_credentials(
        hass, DOMAIN, CLIENT_ID, CLIENT_SECRET, DOMAIN
    )


@fixture
def config_entry() -> MockConfigEntry:
    """Create Google Mail entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        unique_id=TITLE,
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "mock-access-token",
                "refresh_token": "mock-refresh-token",
                "expires_at": time.time() + 3600,
                "scope": " ".join(SCOPES),
            },
        },
    )


@fixture
def mock_connection(
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> Generator[None]:
    """Mock Google Mail connection."""
    aioclient.post(
        GOOGLE_TOKEN_URI,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )
    yield
