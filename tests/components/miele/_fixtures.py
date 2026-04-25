"""Tryke fixtures for the Miele integration."""

from collections.abc import Generator
import time
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.miele.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from .const import CLIENT_ID, CLIENT_SECRET

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx


@fixture
def expires_at() -> float:
    """Set the OAuth token expiration time."""
    return time.time() + 3600


@fixture
def mock_config_entry(
    hass: HomeAssistant = Depends(hass_fx),
    expires_at: float = Depends(expires_at),
) -> MockConfigEntry:
    """Return the default mocked config entry."""
    config_entry = MockConfigEntry(
        minor_version=1,
        domain=DOMAIN,
        title="Miele test",
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "Fake_token",
                "expires_in": 86399,
                "refresh_token": "3012bc9f-7a65-4240-b817-9154ffdcc30f",
                "token_type": "Bearer",
                "expires_at": expires_at,
            },
        },
        entry_id="miele_test",
    )
    config_entry.add_to_hass(hass)
    return config_entry


@fixture
async def setup_credentials(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Set up application credentials."""
    await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
        DOMAIN,
    )


@fixture
def access_token() -> str:
    """Return a valid access token."""
    return "mock-access-token"


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.miele.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry
