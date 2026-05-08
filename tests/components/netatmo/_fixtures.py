"""Tryke fixtures for the Netatmo integration."""

from tryke import Depends, fixture

from homeassistant.components.netatmo.const import DOMAIN
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_application_credentials

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"


@fixture
async def setup_credentials(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up the OAuth2 application_credentials chain."""
    await setup_application_credentials(
        hass, DOMAIN, CLIENT_ID, CLIENT_SECRET, "cloud"
    )
