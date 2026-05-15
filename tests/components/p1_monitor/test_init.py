"""Tests for the P1 Monitor integration."""

from unittest.mock import AsyncMock, patch

from p1monitor import P1MonitorConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.p1_monitor.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from ._fixtures import (
    mock_config_entry,
    mock_p1monitor,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@fixture
def _mock_request_failure():
    """Patch P1Monitor._request to raise."""
    with patch(
        "homeassistant.components.p1_monitor.coordinator.P1Monitor._request",
        side_effect=P1MonitorConnectionError,
    ) as mock_request:
        yield mock_request


@test
async def load_unload_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_p1monitor),
) -> None:
    """Test the P1 Monitor configuration entry loading/unloading."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def config_entry_not_ready(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_request: AsyncMock = Depends(_mock_request_failure),
) -> None:
    """Test the P1 Monitor configuration entry not ready."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_request.call_count).to_equal(1)
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def migration(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_p1monitor),
) -> None:
    """Test config entry version 1 -> 2 migration."""
    entry = MockConfigEntry(
        unique_id="unique_thingy",
        domain=DOMAIN,
        data={CONF_HOST: "example"},
        version=1,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    migrated = hass.config_entries.async_get_entry(entry.entry_id)
    expect(migrated is not None).to_be(True)
    expect(migrated.version).to_equal(2)
    expect(migrated.data).to_equal({CONF_HOST: "example", "port": 80})


@test
async def port_migration(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_p1monitor),
) -> None:
    """Test migration of host:port to separate host and port."""
    entry = MockConfigEntry(
        unique_id="unique_thingy",
        domain=DOMAIN,
        data={CONF_HOST: "example:80"},
        version=1,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    migrated = hass.config_entries.async_get_entry(entry.entry_id)
    expect(migrated is not None).to_be(True)
    expect(migrated.version).to_equal(2)
    expect(migrated.data).to_equal({CONF_HOST: "example", "port": 80})
