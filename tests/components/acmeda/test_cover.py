"""Define tests for the Acmeda cover platform."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.acmeda.const import DOMAIN
from homeassistant.components.cover import DOMAIN as COVER_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import mock_config_entry, mock_hub_run

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
async def cover_id_migration(
    _hub: AsyncMock = Depends(mock_hub_run),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test migrating unique id."""
    entity_registry.async_get_or_create(
        COVER_DOMAIN, DOMAIN, 1234567890123, config_entry=mock_config_entry
    )
    expect(await hass.config_entries.async_setup(mock_config_entry.entry_id)).to_be(
        True
    )

    await hass.async_block_till_done()
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    expect(len(entities)).to_equal(1)
    expect(entities[0].unique_id).to_equal("1234567890123")
