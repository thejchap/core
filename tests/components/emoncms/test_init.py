"""Test Emoncms component setup process."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.emoncms.const import DOMAIN, FEED_ID, FEED_NAME
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, issue_registry as ir

from . import setup_integration
from ._fixtures import (
    EMONCMS_FAILURE,
    FEEDS,
    config_entry as config_entry_fixture,
    emoncms_client as emoncms_client_fixture,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    issue_registry as issue_registry_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Tryke discovery anchor."""


@test
async def load_unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    _emoncms_client: AsyncMock = Depends(emoncms_client_fixture),
) -> None:
    """Test load and unload entry."""
    await setup_integration(hass, config_entry)

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    emoncms_client: AsyncMock = Depends(emoncms_client_fixture),
) -> None:
    """Test load failure."""
    emoncms_client.async_request.return_value = EMONCMS_FAILURE
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(False)


@test
async def migrate_uuid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    emoncms_client: AsyncMock = Depends(emoncms_client_fixture),
) -> None:
    """Test migration from home assistant uuid to emoncms uuid."""
    config_entry.add_to_hass(hass)
    expect(config_entry.unique_id).to_be(None)
    for feed in FEEDS:
        entity_registry.async_get_or_create(
            Platform.SENSOR,
            DOMAIN,
            f"{config_entry.entry_id}-{feed[FEED_ID]}",
            config_entry=config_entry,
            suggested_object_id=f"{DOMAIN}_{feed[FEED_NAME]}",
        )
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    emoncms_uuid = emoncms_client.async_get_uuid.return_value
    expect(config_entry.unique_id).to_equal(emoncms_uuid)
    entity_entries = er.async_entries_for_config_entry(
        entity_registry, config_entry.entry_id
    )

    for nb, feed in enumerate(FEEDS):
        expect(entity_entries[nb].unique_id).to_equal(f"{emoncms_uuid}-{feed[FEED_ID]}")
        expect(entity_entries[nb].previous_unique_id).to_equal(
            f"{config_entry.entry_id}-{feed[FEED_ID]}"
        )


@test
async def no_uuid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
    emoncms_client: AsyncMock = Depends(emoncms_client_fixture),
) -> None:
    """Test an issue is created when the emoncms server does not ship an uuid."""
    emoncms_client.async_get_uuid.return_value = None
    await setup_integration(hass, config_entry)

    expect(
        issue_registry.async_get_issue(domain=DOMAIN, issue_id="migrate database")
        is not None
    ).to_be(True)
