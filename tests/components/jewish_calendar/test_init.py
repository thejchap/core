"""Tests for the Jewish Calendar component's init."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.jewish_calendar.const import DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test.cases(
    test.case("first_light", old_key="first_light", new_key="alot_hashachar"),
    test.case("sunset", old_key="sunset", new_key="shkia"),
    test.case("havdalah_unchanged", old_key="havdalah", new_key="havdalah"),
)
async def migrate_unique_id(
    *,
    old_key: str,
    new_key: str,
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test unique id migration."""
    config_entry.add_to_hass(hass)

    entity: er.RegistryEntry = entity_registry.async_get_or_create(
        domain=SENSOR_DOMAIN,
        platform=DOMAIN,
        unique_id=f"{config_entry.entry_id}-{old_key}",
        config_entry=config_entry,
    )
    expect(entity.unique_id.endswith(f"-{old_key}")).to_be(True)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_migrated = entity_registry.async_get(entity.entity_id)
    expect(entity_migrated is not None).to_be(True)
    expect(entity_migrated.unique_id).to_equal(f"{config_entry.entry_id}-{new_key}")
