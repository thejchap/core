"""Tryke fixtures for iotty config flow tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from aiohttp import ClientSession
from tryke import Depends, fixture

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.iotty.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.setup import async_setup_component

from .conftest import CLIENT_ID, CLIENT_SECRET

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.iotty.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
async def setup_credentials(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Fixture to setup application credentials component."""
    await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
    )


@fixture
async def local_oauth_impl(
    hass: HomeAssistant = Depends(hass_fx),
) -> config_entry_oauth2_flow.LocalOAuth2Implementation:
    """Local OAuth2 implementation for iotty."""
    assert await async_setup_component(hass, "auth", {})
    return config_entry_oauth2_flow.LocalOAuth2Implementation(
        hass,
        DOMAIN,
        "client_id",
        "client_secret",
        "authorize_url",
        "https://token.url",
    )


@fixture
def aiohttp_client_session() -> type[ClientSession]:
    """AIOHTTP client session class.

    Mirrors the pytest fixture used by ``test_api.py`` — note the original
    fixture returns the *class* (not an instance), so the test_api ports do
    too.
    """
    return ClientSession


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="IOTTY00001",
        domain=DOMAIN,
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "refresh_token": "REFRESH_TOKEN",
                "access_token": "ACCESS_TOKEN_1",
                "expires_in": 10,
                "expires_at": 0,
                "token_type": "bearer",
                "random_other_data": "should_stay",
            },
            CONF_HOST: "127.0.0.1",
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
            CONF_PORT: 9123,
        },
        unique_id="IOTTY00001",
    )


@fixture
def mock_get_devices_nodevices() -> Generator[AsyncMock]:
    """Mock get_devices, returning no devices."""
    with patch("iottycloud.cloudapi.CloudApi.get_devices") as mock_fn:
        yield mock_fn
