"""Tryke fixtures for the Honeywell Lyric integration."""

from tryke import Depends, fixture

from homeassistant.components.application_credentials import (
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.lyric.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"


@fixture
async def mock_impl(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Mock implementation."""
    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    await async_import_client_credential(
        hass, DOMAIN, ClientCredential(CLIENT_ID, CLIENT_SECRET), "cred"
    )
