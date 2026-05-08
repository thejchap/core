"""Test the Portainer initial specific behavior."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.portainer.const import DOMAIN
from homeassistant.const import (
    CONF_API_KEY,
    CONF_API_TOKEN,
    CONF_HOST,
    CONF_URL,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant

from ._fixtures import TEST_INSTANCE_ID, mock_portainer_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Force tryke to fully resolve hass before each test."""


@test
async def migrations(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    portainer_client: AsyncMock = Depends(mock_portainer_client),
) -> None:
    """Test migration from v1 config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "http://test_host",
            CONF_API_KEY: "test_key",
        },
        unique_id="1",
        version=1,
    )
    entry.add_to_hass(hass)
    expect(entry.version).to_equal(1)
    expect(CONF_VERIFY_SSL not in entry.data).to_be(True)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(CONF_HOST not in entry.data).to_be(True)
    expect(CONF_API_KEY not in entry.data).to_be(True)
    expect(entry.data[CONF_URL]).to_equal("http://test_host")
    expect(entry.data[CONF_API_TOKEN]).to_equal("test_key")
    expect(entry.data[CONF_VERIFY_SSL]).to_be(True)
    expect(entry.version).to_equal(5)
    expect(entry.unique_id).to_equal(TEST_INSTANCE_ID)


@test.skip("indirect parametrize + needs syrupy snapshot - port deferred")
async def setup_exceptions() -> None:
    """Stub for test_setup_exceptions (port deferred)."""

@test.skip("syrupy snapshot")
async def remove_config_entry_device() -> None:
    """Stub for test_remove_config_entry_device (port deferred)."""

@test.skip("syrupy snapshot")
async def migration_v3_to_v5() -> None:
    """Stub for test_migration_v3_to_v5 (port deferred)."""

@test.skip("syrupy snapshot")
async def migration_v4_to_v5() -> None:
    """Stub for test_migration_v4_to_v5 (port deferred)."""

@test.skip("syrupy snapshot")
async def migration_v4_to_v5_exceptions() -> None:
    """Stub for test_migration_v4_to_v5_exceptions (port deferred)."""

@test.skip("syrupy snapshot")
async def device_registry() -> None:
    """Stub for test_device_registry (port deferred)."""

@test.skip("syrupy snapshot")
async def container_stack_device_links() -> None:
    """Stub for test_container_stack_device_links (port deferred)."""

@test.skip("syrupy snapshot")
async def new_endpoint_callback() -> None:
    """Stub for test_new_endpoint_callback (port deferred)."""

@test.skip("syrupy snapshot")
async def new_container_callback() -> None:
    """Stub for test_new_container_callback (port deferred)."""

@test.skip("syrupy snapshot")
async def swarm_stacks_fetched_by_swarm_id() -> None:
    """Stub for test_swarm_stacks_fetched_by_swarm_id (port deferred)."""

@test.skip("syrupy snapshot")
async def new_stack_callback() -> None:
    """Stub for test_new_stack_callback (port deferred)."""
