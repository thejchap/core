"""Test the Foscam component."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.foscam.const import DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .conftest import setup_mock_foscam_camera
from .const import ENTRY_ID, VALID_CONFIG

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    entity_registry,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test
async def unique_id_new_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ent_reg: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test unique ID for a newly added device is correct."""
    entry = MockConfigEntry(domain=DOMAIN, data=VALID_CONFIG, entry_id=ENTRY_ID)
    entry.add_to_hass(hass)

    with (
        # Mock a valid camera instance
        patch("homeassistant.components.foscam.FoscamCamera") as mock_foscam_camera,
    ):
        setup_mock_foscam_camera(mock_foscam_camera)
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)

    await hass.async_block_till_done()

    # Test that unique_id remains the same.
    entity_id = ent_reg.async_get_entity_id(
        SWITCH_DOMAIN, DOMAIN, f"{ENTRY_ID}_sleep_switch"
    )
    entity_new = ent_reg.async_get(entity_id)
    expect(entity_new.unique_id).to_equal(f"{ENTRY_ID}_sleep_switch")


@test
async def switch_unique_id_migration_ok(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ent_reg: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test that the unique ID for a sleep switch is migrated to the new format."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=VALID_CONFIG, entry_id=ENTRY_ID, version=1
    )
    entry.add_to_hass(hass)

    entity_before = ent_reg.async_get_or_create(
        SWITCH_DOMAIN, DOMAIN, "sleep_switch", config_entry=entry
    )
    expect(entity_before.unique_id).to_equal("sleep_switch")

    # Update config entry with version 2
    entry = MockConfigEntry(
        domain=DOMAIN, data=VALID_CONFIG, entry_id=ENTRY_ID, version=2
    )
    entry.add_to_hass(hass)

    with (
        # Mock a valid camera instance
        patch("homeassistant.components.foscam.FoscamCamera") as mock_foscam_camera,
    ):
        setup_mock_foscam_camera(mock_foscam_camera)
        await hass.config_entries.async_setup(entry.entry_id)

    await hass.async_block_till_done()

    entity_id_new = ent_reg.async_get_entity_id(
        SWITCH_DOMAIN, DOMAIN, f"{ENTRY_ID}_sleep_switch"
    )
    expect(hass.states.get(entity_id_new) is not None).to_be(True)
    entity_after = ent_reg.async_get(entity_id_new)
    expect(entity_after.previous_unique_id).to_equal("sleep_switch")
    expect(entity_after.unique_id).to_equal(f"{ENTRY_ID}_sleep_switch")


@test
async def unique_id_migration_not_needed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ent_reg: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test that the unique ID for a sleep switch is not executed if already in right format."""
    entry = MockConfigEntry(domain=DOMAIN, data=VALID_CONFIG, entry_id=ENTRY_ID)
    entry.add_to_hass(hass)

    ent_reg.async_get_or_create(
        SWITCH_DOMAIN, DOMAIN, f"{ENTRY_ID}_sleep_switch", config_entry=entry
    )

    entity_id = ent_reg.async_get_entity_id(
        SWITCH_DOMAIN, DOMAIN, f"{ENTRY_ID}_sleep_switch"
    )
    entity_before = ent_reg.async_get(entity_id)
    expect(entity_before.unique_id).to_equal(f"{ENTRY_ID}_sleep_switch")

    with (
        # Mock a valid camera instance
        patch("homeassistant.components.foscam.FoscamCamera") as mock_foscam_camera,
        patch(
            "homeassistant.components.foscam.async_migrate_entry",
            return_value=True,
        ),
    ):
        setup_mock_foscam_camera(mock_foscam_camera)
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)

    await hass.async_block_till_done()

    # Test that unique_id remains the same.
    expect(hass.states.get(entity_id) is not None).to_be(True)
    entity_after = ent_reg.async_get(entity_id)
    expect(entity_after.unique_id).to_equal(entity_before.unique_id)
