"""The init tests for the UPB platform."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.upb.const import DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def migrate_entry_minor_version_1_2(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test migrating a 1.1 config entry to 1.2."""
    with patch("homeassistant.components.upb.async_setup_entry", return_value=True):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={"protocol": "TCP", "address": "1.2.3.4", "file_path": "upb.upe"},
            version=1,
            minor_version=1,
            unique_id=123456,
        )
        entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be_truthy()
        expect(entry.version).to_equal(1)
        expect(entry.minor_version).to_equal(2)
        expect(entry.unique_id).to_equal("123456")
