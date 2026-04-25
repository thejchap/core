"""Tryke fixtures for the senz integration."""

import time

from tryke import Depends, fixture

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.senz.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.setup import async_setup_component

from .const import CLIENT_ID, CLIENT_SECRET, ENTRY_UNIQUE_ID

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx


@fixture
def expires_at() -> float:
    """Fixture to set the oauth token expiration time."""
    return time.time() + 3600


@fixture
def mock_config_entry(
    hass: HomeAssistant = Depends(hass_fx),
    expires_at: float = Depends(expires_at),
) -> MockConfigEntry:
    """Return the default mocked config entry."""
    config_entry = MockConfigEntry(
        minor_version=2,
        domain=DOMAIN,
        title="Senz test",
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
        entry_id="senz_test",
        unique_id=ENTRY_UNIQUE_ID,
    )
    config_entry.add_to_hass(hass)
    return config_entry


@fixture
async def setup_credentials(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Fixture to setup credentials."""
    assert await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(
            CLIENT_ID,
            CLIENT_SECRET,
        ),
        DOMAIN,
    )


@fixture
def unique_id() -> str:
    """Return a unique ID."""
    return ENTRY_UNIQUE_ID


@fixture
async def access_token(
    hass: HomeAssistant = Depends(hass_fx),
    unique_id: str = Depends(unique_id),
) -> str:
    """Return a valid access token."""
    return config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "sub": unique_id,
            "aud": [],
            "scp": [
                "rest_api",
                "offline_access",
            ],
            "ou_code": "NA",
        },
    )
