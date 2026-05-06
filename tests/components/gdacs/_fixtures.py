"""Tryke fixtures for GDACS tests."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture

from homeassistant.components.gdacs.const import CONF_CATEGORIES, DOMAIN
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
    CONF_SCAN_INTERVAL,
    CONF_UNIT_SYSTEM,
)

from tests.common import MockConfigEntry


@fixture
def gdacs_setup() -> Generator[None]:
    """Mock gdacs entry setup."""
    with patch("homeassistant.components.gdacs.async_setup_entry", return_value=True):
        yield


@fixture
def config_entry() -> MockConfigEntry:
    """Create a mock GDACS config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_LATITUDE: -41.2,
            CONF_LONGITUDE: 174.7,
            CONF_RADIUS: 25,
            CONF_UNIT_SYSTEM: "metric",
            CONF_SCAN_INTERVAL: 300.0,
            CONF_CATEGORIES: [],
        },
        title="-41.2, 174.7",
        unique_id="-41.2, 174.7",
    )
