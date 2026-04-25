"""Tryke fixtures for the google_sheets integration."""

from collections.abc import Generator
from unittest.mock import Mock, patch

from tryke import Depends, fixture

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.google_sheets.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fx

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"


@fixture
async def setup_credentials(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Fixture to setup credentials."""
    assert await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
    )


@fixture
def mock_client() -> Generator[Mock]:
    """Fixture to setup a fake spreadsheet client library."""
    with patch(
        "homeassistant.components.google_sheets.config_flow.Client"
    ) as mock_client:
        yield mock_client
