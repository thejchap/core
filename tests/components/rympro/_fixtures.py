"""Tryke fixtures for the rympro integration."""

from tryke import Depends, fixture

from homeassistant.components.rympro.const import DOMAIN
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TOKEN, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx

TEST_DATA = {
    CONF_EMAIL: "test-email",
    CONF_PASSWORD: "test-password",
    CONF_TOKEN: "test-token",
    CONF_UNIQUE_ID: "test-account-number",
}


@fixture
def mock_config_entry(
    hass: HomeAssistant = Depends(hass_fx),
) -> MockConfigEntry:
    """Create a mock config entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=TEST_DATA,
        unique_id=TEST_DATA[CONF_UNIQUE_ID],
    )
    config_entry.add_to_hass(hass)
    return config_entry
