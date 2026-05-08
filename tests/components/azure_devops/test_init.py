"""Tests for init of Azure DevOps."""

from unittest.mock import AsyncMock, MagicMock

import aiohttp
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_config_entry, mock_devops_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
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
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_devops_client: MagicMock = Depends(mock_devops_client),
) -> None:
    """Test a successful setup entry."""
    expect(await setup_integration(hass, mock_config_entry)).to_be(True)

    expect(bool(mock_devops_client.authorized)).to_be(True)
    expect(mock_devops_client.authorize.call_count).to_equal(1)
    expect(mock_devops_client.get_builds.call_count).to_equal(1)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_remove(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def auth_failed(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_devops_client: AsyncMock = Depends(mock_devops_client),
) -> None:
    """Test a failed setup entry."""
    mock_devops_client.authorize.return_value = False
    mock_devops_client.authorized = False

    await setup_integration(hass, mock_config_entry)

    expect(bool(mock_devops_client.authorized)).to_be(False)

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def update_failed_project(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_devops_client: MagicMock = Depends(mock_devops_client),
) -> None:
    """Test a failed update entry."""
    mock_devops_client.get_project.side_effect = aiohttp.ClientError

    await setup_integration(hass, mock_config_entry)

    expect(mock_devops_client.get_project.call_count).to_equal(1)

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def update_failed_builds(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_devops_client: MagicMock = Depends(mock_devops_client),
) -> None:
    """Test a failed update entry."""
    mock_devops_client.get_builds.side_effect = aiohttp.ClientError

    await setup_integration(hass, mock_config_entry)

    expect(mock_devops_client.get_builds.call_count).to_equal(1)

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def no_builds(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_devops_client: MagicMock = Depends(mock_devops_client),
) -> None:
    """Test a failed update entry."""
    mock_devops_client.get_builds.return_value = None

    await setup_integration(hass, mock_config_entry)

    expect(mock_devops_client.get_builds.call_count).to_equal(1)

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def no_work_item_types(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_devops_client: MagicMock = Depends(mock_devops_client),
) -> None:
    """Test a failed update entry."""
    mock_devops_client.get_work_item_types.return_value = None

    await setup_integration(hass, mock_config_entry)

    expect(mock_devops_client.get_work_item_types.call_count).to_equal(1)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def no_work_item_ids(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_devops_client: MagicMock = Depends(mock_devops_client),
) -> None:
    """Test a failed update entry."""
    mock_devops_client.get_work_item_ids.return_value = None

    await setup_integration(hass, mock_config_entry)

    expect(mock_devops_client.get_work_item_ids.call_count).to_equal(1)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def no_work_items(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_devops_client: MagicMock = Depends(mock_devops_client),
) -> None:
    """Test a failed update entry."""
    mock_devops_client.get_work_items.return_value = None

    await setup_integration(hass, mock_config_entry)

    expect(mock_devops_client.get_work_items.call_count).to_equal(1)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
