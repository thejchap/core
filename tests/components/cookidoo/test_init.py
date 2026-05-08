"""Unit tests for the cookidoo integration."""

from unittest.mock import AsyncMock

from cookidoo_api import CookidooAuthException, CookidooRequestException
from tryke import Depends, expect, fixture, test

from homeassistant.components.cookidoo.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import (
    cookidoo_config_entry as cookidoo_config_entry_fixture,
    mock_cookidoo_client,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def load_unload(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_cookidoo_client),
    cookidoo_config_entry: MockConfigEntry = Depends(cookidoo_config_entry_fixture),
) -> None:
    """Test loading and unloading of the config entry."""
    await setup_integration(hass, cookidoo_config_entry)

    entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(entries)).to_equal(1)

    expect(cookidoo_config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(cookidoo_config_entry.entry_id)).to_be(True)
    expect(cookidoo_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case(
        "request_exception",
        exception=CookidooRequestException,
        status=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "auth_exception",
        exception=CookidooAuthException,
        status=ConfigEntryState.SETUP_ERROR,
    ),
)
async def init_failure(
    *,
    exception: type[Exception],
    status: ConfigEntryState,
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_cookidoo_client: AsyncMock = Depends(mock_cookidoo_client),
    cookidoo_config_entry: MockConfigEntry = Depends(cookidoo_config_entry_fixture),
) -> None:
    """Test an initialization error on integration load."""
    mock_cookidoo_client.login.side_effect = exception
    await setup_integration(hass, cookidoo_config_entry)
    expect(cookidoo_config_entry.state).to_equal(status)


@test.cases(
    test.case("get_ingredient_items", method="get_ingredient_items"),
    test.case("get_additional_items", method="get_additional_items"),
)
async def config_entry_not_ready(
    *,
    method: str,
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cookidoo_config_entry: MockConfigEntry = Depends(cookidoo_config_entry_fixture),
    mock_cookidoo_client: AsyncMock = Depends(mock_cookidoo_client),
) -> None:
    """Test config entry not ready."""
    getattr(mock_cookidoo_client, method).side_effect = CookidooRequestException()
    cookidoo_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(cookidoo_config_entry.entry_id)
    await hass.async_block_till_done()
    expect(cookidoo_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def config_entry_not_ready_auth_error(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cookidoo_config_entry: MockConfigEntry = Depends(cookidoo_config_entry_fixture),
    mock_cookidoo_client: AsyncMock = Depends(mock_cookidoo_client),
) -> None:
    """Test config entry not ready from authentication error."""
    mock_cookidoo_client.login.side_effect = CookidooAuthException()
    cookidoo_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(cookidoo_config_entry.entry_id)
    await hass.async_block_till_done()
    expect(cookidoo_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test.skip("complex migration test with parametrize over registry state")
async def migration_from() -> None:
    """Stub for test_migration_from."""


@test.skip("complex migration test with parametrize over registry state")
async def migration_from_with_error() -> None:
    """Stub for test_migration_from_with_error."""
