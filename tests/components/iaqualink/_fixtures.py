"""Tryke fixtures for the iaqualink integration."""

from unittest.mock import AsyncMock

from tryke import fixture

from homeassistant.components.iaqualink import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry

MOCK_USERNAME = "test@example.com"
MOCK_PASSWORD = "password"
MOCK_DATA = {CONF_USERNAME: MOCK_USERNAME, CONF_PASSWORD: MOCK_PASSWORD}


def async_returns(x):  # noqa: ANN001, ANN201
    """Return value-returning async mock."""
    return AsyncMock(return_value=x)


def async_raises(x):  # noqa: ANN001, ANN201
    """Return exception-raising async mock."""
    return AsyncMock(side_effect=x)


@fixture
def config_data() -> dict[str, str]:
    """Create hass config fixture."""
    return MOCK_DATA


@fixture
def config() -> dict[str, dict[str, str]]:
    """Create hass config fixture."""
    return {DOMAIN: MOCK_DATA}


@fixture
def config_entry() -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_DATA,
    )
