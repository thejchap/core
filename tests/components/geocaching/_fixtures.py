"""Tryke fixtures for the Geocaching integration."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from geocachingapi import GeocachingStatus
from tryke import Depends, fixture

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.geocaching.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import CLIENT_ID, CLIENT_SECRET

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="1234AB 1",
        domain=DOMAIN,
        data={
            "id": "mock_user",
            "auth_implementation": DOMAIN,
        },
        unique_id="mock_user",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.geocaching.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_geocaching_config_flow() -> Generator[MagicMock]:
    """Return a mocked Geocaching API client."""

    mock_status = GeocachingStatus()
    mock_status.user.username = "mock_user"

    with patch(
        "homeassistant.components.geocaching.config_flow.GeocachingApi", autospec=True
    ) as geocaching_mock:
        geocachingapi = geocaching_mock.return_value
        geocachingapi.update.return_value = mock_status
        yield geocachingapi


@fixture
async def setup_credentials(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Set up application credentials so the OAuth flow finds the client id."""
    await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
    )
