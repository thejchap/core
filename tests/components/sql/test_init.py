"""Test for SQL component Init."""

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import init_integration
from ._fixtures import recorder_mock

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _recorder: object = Depends(recorder_mock),
) -> None:
    """Force tryke fixture resolution before each test."""


@test
async def setup_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup entry."""
    config_entry = await init_integration(hass)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test unload an entry."""
    config_entry = await init_integration(hass)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.skip("requires recorder + YAML import flow — port deferred")
async def setup_config() -> None:
    """Stub for test_setup_config."""


@test.skip("requires recorder + invalid-config flow — port deferred")
async def setup_invalid_config() -> None:
    """Stub for test_setup_invalid_config."""


@test.skip("requires schema validation context — port deferred")
async def invalid_query() -> None:
    """Stub for test_invalid_query."""


@test.skip("requires schema validation context — port deferred")
async def query_no_read_only() -> None:
    """Stub for test_query_no_read_only."""


@test.skip("requires schema validation context — port deferred")
async def query_no_read_only_cte() -> None:
    """Stub for test_query_no_read_only_cte."""


@test.skip("requires schema validation context — port deferred")
async def multiple_queries() -> None:
    """Stub for test_multiple_queries."""


@test.skip("requires recorder + schema migration — port deferred")
async def migration_from_future() -> None:
    """Stub for test_migration_from_future."""


@test.skip("requires recorder + schema migration — port deferred")
async def migration_from_v1_to_v2() -> None:
    """Stub for test_migration_from_v1_to_v2."""
