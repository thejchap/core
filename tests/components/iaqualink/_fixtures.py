"""Tryke fixtures for iAqualink."""

from __future__ import annotations

from tryke import fixture

from homeassistant.components.iaqualink import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry

MOCK_USERNAME = "test@example.com"
MOCK_PASSWORD = "password"
MOCK_DATA = {CONF_USERNAME: MOCK_USERNAME, CONF_PASSWORD: MOCK_PASSWORD}


@fixture
def config_data() -> dict[str, str]:
    """Create hass config fixture."""
    return MOCK_DATA


@fixture
def config_entry() -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_DATA,
    )
