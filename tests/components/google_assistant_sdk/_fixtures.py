"""Tryke fixtures for the Google Assistant SDK integration."""

from collections.abc import Awaitable, Callable, Coroutine
import time
from typing import Any

from tryke import Depends, fixture

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.google_assistant_sdk.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx

type ComponentSetup = Callable[[], Awaitable[None]]

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"
ACCESS_TOKEN = "mock-access-token"


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
def scopes() -> list[str]:
    """Set the scopes present in the OAuth token."""
    return ["https://www.googleapis.com/auth/assistant-sdk-prototype"]


@fixture
def expires_at() -> int:
    """Set the oauth token expiration time."""
    return int(time.time() + 3600)


@fixture
def config_entry(
    expires_at: int = Depends(expires_at),
    scopes: list[str] = Depends(scopes),
) -> MockConfigEntry:
    """MockConfigEntry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": ACCESS_TOKEN,
                "refresh_token": "mock-refresh-token",
                "expires_at": expires_at,
                "scope": " ".join(scopes),
            },
        },
    )


@fixture
async def setup_integration(
    hass: HomeAssistant = Depends(hass_fx),
    entry: MockConfigEntry = Depends(config_entry),
    _credentials: None = Depends(setup_credentials),
) -> Callable[[], Coroutine[Any, Any, None]]:
    """Set up the integration."""
    entry.add_to_hass(hass)

    async def func() -> None:
        await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()

    return func
