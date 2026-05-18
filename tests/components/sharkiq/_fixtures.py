"""Tryke fixtures for the Shark IQ integration tests."""

from collections.abc import AsyncGenerator, Iterable
from copy import deepcopy
from datetime import datetime, timedelta
import enum
from unittest.mock import patch

from sharkiq import AylaApi, SharkIqVacuum
from tryke import Depends, fixture

from homeassistant.components.sharkiq.const import DOMAIN
from homeassistant.core import HomeAssistant

from .const import (
    CONFIG,
    ENTRY_ID,
    SHARK_DEVICE_DICT,
    SHARK_METADATA_DICT,
    SHARK_PROPERTIES_DICT,
    TEST_USERNAME,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

ROOM_LIST = ["Kitchen", "Living Room"]


class MockAyla(AylaApi):
    """Mocked AylaApi that doesn't do anything."""

    desired_expiry = False

    async def async_sign_in(self):
        """Instead of signing in, just return."""

    async def async_set_cookie(self):
        """Instead of getting cookies, just return."""

    async def async_refresh_auth(self):
        """Instead of refreshing auth, just return."""

    async def async_sign_out(self):
        """Instead of signing out, just return."""

    async def async_list_devices(self) -> list[dict]:
        """Return the device list."""
        return [SHARK_DEVICE_DICT]

    async def async_get_devices(self, update: bool = True) -> list[SharkIqVacuum]:
        """Get the list of devices."""
        shark = MockShark(self, SHARK_DEVICE_DICT)
        shark.properties_full = deepcopy(SHARK_PROPERTIES_DICT)
        shark._update_metadata(SHARK_METADATA_DICT)
        return [shark]

    async def async_request(self, http_method: str, url: str, **kwargs):
        """Don't make an HTTP request."""

    @property
    def token_expiring_soon(self) -> bool:
        """Toggling Property for Token Expiration Flag."""
        # Alternate expiry flag for each test
        self.desired_expiry = not self.desired_expiry
        return self.desired_expiry

    @property
    def auth_expiration(self) -> datetime:
        """Sample expiration timestamp that is always 1200 seconds behind now()."""
        return datetime.now() - timedelta(seconds=1200)


class MockShark(SharkIqVacuum):
    """Mocked SharkIqVacuum that won't hit the API."""

    async def async_update(self, property_list: Iterable[str] | None = None):
        """Don't do anything."""

    def set_property_value(self, property_name, value):
        """Set a property locally without hitting the API."""
        if isinstance(property_name, enum.Enum):
            property_name = property_name.value
        if isinstance(value, enum.Enum):
            value = value.value
        self.properties_full[property_name]["value"] = value

    async def async_set_property_value(self, property_name, value):
        """Set a property locally without hitting the API."""
        self.set_property_value(property_name, value)

    def get_room_list(self):
        """Return the list of available rooms without hitting the API."""
        return ROOM_LIST


@fixture
async def setup_integration(
    hass: HomeAssistant = Depends(hass_fixture),
) -> AsyncGenerator[HomeAssistant]:
    """Build the mock integration."""
    with patch("sharkiq.ayla_api.AylaApi", MockAyla):
        entry = MockConfigEntry(
            domain=DOMAIN, unique_id=TEST_USERNAME, data=CONFIG, entry_id=ENTRY_ID
        )
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        yield hass
