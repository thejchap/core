"""Tryke fixtures for the Google Tasks integration."""

from collections.abc import Generator
from unittest.mock import Mock, patch

from tryke import Depends, fixture

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.google_tasks.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fx

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"


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
def setup_userinfo() -> Generator[Mock]:
    """Set up userinfo with default user id 123."""
    with patch("homeassistant.components.google_tasks.config_flow.build") as mock:
        mock.return_value.userinfo.return_value.get.return_value.execute.return_value = {
            "id": "123",
            "name": "Test Name",
        }
        yield mock
