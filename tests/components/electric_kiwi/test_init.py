"""Test the Electric Kiwi init."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.electric_kiwi.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import init_integration
from ._fixtures import (
    config_entry,
    config_entry2,
    electrickiwi_api,
    setup_credentials,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _creds: None = Depends(setup_credentials),
) -> None:
    """Anchor for tryke fixture resolution + creds."""


@test
async def async_setup_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    _api: AsyncMock = Depends(electrickiwi_api),
) -> None:
    """Test a successful setup entry and unload of entry."""
    await init_integration(hass, entry)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def async_setup_multiple_entries(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    entry2: MockConfigEntry = Depends(config_entry2),
    _api: AsyncMock = Depends(electrickiwi_api),
) -> None:
    """Test a successful setup and unload of multiple entries."""

    for e in (entry, entry2):
        await init_integration(hass, e)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(2)

    for e in (entry, entry2):
        expect(await hass.config_entries.async_unload(e.entry_id)).to_be(True)
        await hass.async_block_till_done()
        expect(e.state).to_be(ConfigEntryState.NOT_LOADED)


@test.skip("requires API exception parametrize + reauth flow")
async def setup_entry_exceptions() -> None:
    """Stub for test_setup_entry_exceptions."""


@test.skip("requires entity migration assertions")
async def migrate_entity_unique_id() -> None:
    """Stub for test_migrate_entity_unique_id."""


@test.skip("requires entity migration with conflicts")
async def migrate_entity_unique_id_conflict() -> None:
    """Stub for test_migrate_entity_unique_id_conflict."""


@test.skip("requires migrated_config_entry full setup")
async def migrate_entry() -> None:
    """Stub for test_migrate_entry."""
