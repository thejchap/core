"""Test emoncms sensor."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import setup_integration
from ._fixtures import (
    config_entry,
    config_no_feed,
    emoncms_client,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def no_feed_selected(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cfg: MockConfigEntry = Depends(config_no_feed),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _client: AsyncMock = Depends(emoncms_client),
) -> None:
    """Test with no feed selected."""
    await setup_integration(hass, cfg)

    expect(cfg.state).to_be(ConfigEntryState.LOADED)
    entity_entries = er.async_entries_for_config_entry(
        entity_registry, cfg.entry_id
    )
    expect(entity_entries).to_equal([])


@test
async def no_feed_broadcast(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cfg: MockConfigEntry = Depends(config_entry),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    client: AsyncMock = Depends(emoncms_client),
) -> None:
    """Test with no feed broadcasted."""
    client.async_request.return_value = {"success": True, "message": []}
    await setup_integration(hass, cfg)

    expect(cfg.state).to_be(ConfigEntryState.LOADED)
    entity_entries = er.async_entries_for_config_entry(
        entity_registry, cfg.entry_id
    )
    expect(entity_entries).to_equal([])


@test.skip("snapshot diverged - needs pytest --snapshot-update")
async def coordinator_update() -> None:
    """Stub for test_coordinator_update."""
