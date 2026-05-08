"""Test pyLoad init."""

from __future__ import annotations

from unittest.mock import MagicMock

from pyloadapi.exceptions import CannotConnect, InvalidAuth, ParserError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import CONF_PATH, CONF_URL
from homeassistant.core import HomeAssistant

from ._fixtures import (
    config_entry as config_entry_fx,
    config_entry_migrate as config_entry_migrate_fx,
    mock_pyloadapi as mock_pyloadapi_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def entry_setup_unload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    _mock_pyloadapi: MagicMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test integration setup and unload."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case("cannot_connect", side_effect=CannotConnect),
    test.case("parser_error", side_effect=ParserError),
)
async def config_entry_setup_errors(
    side_effect: type[Exception],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    mock_pyloadapi: MagicMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test config entry not ready."""
    mock_pyloadapi.version.side_effect = side_effect
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def config_entry_setup_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    mock_pyloadapi: MagicMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test config entry authentication."""
    mock_pyloadapi.version.side_effect = InvalidAuth
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
    expect(any(config_entry.async_get_active_flows(hass, {SOURCE_REAUTH}))).to_be(True)


@test
async def coordinator_update_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    mock_pyloadapi: MagicMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test coordinator authentication."""
    mock_pyloadapi.get_status.side_effect = InvalidAuth

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
    expect(any(config_entry.async_get_active_flows(hass, {SOURCE_REAUTH}))).to_be(True)


@test
async def coordinator_setup_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    mock_pyloadapi: MagicMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test coordinator setup authentication."""
    mock_pyloadapi.version.side_effect = InvalidAuth

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
    expect(any(config_entry.async_get_active_flows(hass, {SOURCE_REAUTH}))).to_be(True)


@test.cases(
    test.case(
        "cannot_connect",
        exception=CannotConnect,
        state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "invalid_auth",
        exception=InvalidAuth,
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "parser_error",
        exception=ParserError,
        state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def coordinator_update_errors(
    exception: type[Exception],
    state: ConfigEntryState,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    mock_pyloadapi: MagicMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test coordinator update errors."""
    mock_pyloadapi.get_status.side_effect = exception

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(state)


@test
async def migration(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry_migrate: MockConfigEntry = Depends(config_entry_migrate_fx),
    _mock_pyloadapi: MagicMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test config entry migration."""
    config_entry_migrate.add_to_hass(hass)
    expect(config_entry_migrate.data.get(CONF_PATH)).to_be(None)

    await hass.config_entries.async_setup(config_entry_migrate.entry_id)
    await hass.async_block_till_done()

    expect(config_entry_migrate.state).to_be(ConfigEntryState.LOADED)
    expect(config_entry_migrate.version).to_equal(1)
    expect(config_entry_migrate.minor_version).to_equal(1)
    expect(config_entry_migrate.data[CONF_URL]).to_equal("https://pyload.local:8000/")
