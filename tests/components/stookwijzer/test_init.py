"""Test the Stookwijzer init."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.stookwijzer.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, issue_registry as ir

from ._fixtures import (
    mock_config_entry,
    mock_stookwijzer,
    mock_v1_config_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    issue_registry as issue_registry_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def load_unload_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_stookwijzer: MagicMock = Depends(mock_stookwijzer),
) -> None:
    """Test the Stookwijzer configuration entry loading and unloading."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(len(mock_stookwijzer.return_value.async_update.mock_calls)).to_equal(1)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def config_entry_not_ready(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_stookwijzer: MagicMock = Depends(mock_stookwijzer),
) -> None:
    """Test the Stookwijzer configuration entry loading and unloading."""
    mock_stookwijzer.return_value.advice = None

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
    expect(len(mock_stookwijzer.return_value.async_update.mock_calls)).to_equal(1)


@test
async def migrate_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_v1_config_entry: MockConfigEntry = Depends(mock_v1_config_entry),
    mock_stookwijzer: MagicMock = Depends(mock_stookwijzer),
) -> None:
    """Test successful migration of entry data."""
    expect(mock_v1_config_entry.version).to_equal(1)

    mock_v1_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_v1_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_v1_config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(len(mock_stookwijzer.async_transform_coordinates.mock_calls)).to_equal(1)

    expect(mock_v1_config_entry.version).to_equal(2)
    expect(mock_v1_config_entry.data).to_equal(
        {
            CONF_LATITUDE: 450000.123456789,
            CONF_LONGITUDE: 200000.123456789,
        }
    )


@test
async def entry_migration_failure(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_v1_config_entry: MockConfigEntry = Depends(mock_v1_config_entry),
    mock_stookwijzer: MagicMock = Depends(mock_stookwijzer),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test successful migration of entry data."""
    expect(mock_v1_config_entry.version).to_equal(1)

    mock_stookwijzer.async_transform_coordinates.return_value = None

    mock_v1_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_v1_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_v1_config_entry.state).to_be(ConfigEntryState.MIGRATION_ERROR)
    expect(
        issue_registry.async_get_issue(DOMAIN, "location_migration_failed")
    ).not_.to_be(None)

    expect(len(mock_stookwijzer.async_transform_coordinates.mock_calls)).to_equal(1)


@test
async def entity_entry_migration(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_stookwijzer: MagicMock = Depends(mock_stookwijzer),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test successful migration of entry data."""
    mock_config_entry.add_to_hass(hass)
    entity = entity_registry.async_get_or_create(
        suggested_object_id="advice",
        disabled_by=None,
        domain=SENSOR_DOMAIN,
        platform=DOMAIN,
        unique_id=mock_config_entry.entry_id,
        config_entry=mock_config_entry,
    )

    expect(entity.unique_id).to_equal(mock_config_entry.entry_id)

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(
        entity_registry.async_get_entity_id(
            SENSOR_DOMAIN,
            DOMAIN,
            mock_config_entry.entry_id,
        )
    ).to_be(None)

    expect(
        entity_registry.async_get_entity_id(
            SENSOR_DOMAIN,
            DOMAIN,
            f"{mock_config_entry.entry_id}_advice",
        )
    ).to_equal("sensor.advice")
