"""Test the Home Assistant analytics init module."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.analytics_insights import CONF_TRACKED_APPS
from homeassistant.components.analytics_insights.const import (
    CONF_TRACKED_INTEGRATIONS,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import setup_integration
from ._fixtures import mock_analytics_client, mock_config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import mock_async_zeroconf


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zc: None = Depends(mock_async_zeroconf),
) -> None:
    """Per-module trigger to anchor fixture resolution."""


@test
async def load_unload_entry(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_analytics_client: AsyncMock = Depends(mock_analytics_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test load and unload entry."""
    await setup_integration(hass, mock_config_entry)
    entry = hass.config_entries.async_entries(DOMAIN)[0]

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def migration_v1_to_v2(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_analytics_client: AsyncMock = Depends(mock_analytics_client),
) -> None:
    """Test migration from version 1 to 2 change to app_."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=1,
        title="Home Assistant Analytics migration time!",
        data={},
        options={
            "tracked_addons": ["core_samba"],
            CONF_TRACKED_INTEGRATIONS: ["youtube"],
        },
    )
    entry.add_to_hass(hass)
    expect(entry.version).to_equal(1)

    addon_entity_samba = entity_registry.async_get_or_create(
        domain="sensor",
        platform=DOMAIN,
        unique_id="addon_core_samba_active_installations",
        config_entry=entry,
        original_name="Samba Active Installations",
    )

    core_entity = entity_registry.async_get_or_create(
        domain="sensor",
        platform=DOMAIN,
        unique_id="core_youtube_active_installations",
        config_entry=entry,
        original_name="YouTube Active Installations",
    )

    expect(addon_entity_samba.unique_id).to_equal(
        "addon_core_samba_active_installations"
    )
    expect(core_entity.unique_id).to_equal("core_youtube_active_installations")

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.version).to_equal(2)

    addon_entity_samba_after = entity_registry.async_get(addon_entity_samba.entity_id)
    core_entity_after = entity_registry.async_get(core_entity.entity_id)

    expect(addon_entity_samba_after.unique_id).to_equal(
        "app_core_samba_active_installations"
    )
    expect(core_entity_after.unique_id).to_equal(
        "core_youtube_active_installations"
    )

    expect("tracked_addons" in entry.options).to_be(False)
    expect(entry.options[CONF_TRACKED_APPS]).to_equal(["core_samba"])
