"""Tests for the Filesize integration."""

from pathlib import Path

from tryke import Depends, expect, fixture, test

from homeassistant.components.filesize.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_FILE_PATH
from homeassistant.core import HomeAssistant

from . import async_create_file
from ._fixtures import mock_config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    hass as hass_fixture,
    mock_network,
    tmp_path as tmp_path_fixture,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def load_unload_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test the Filesize configuration entry loading/unloading."""
    testfile = str(tmp_path.joinpath("file.txt"))
    await async_create_file(hass, testfile)
    hass.config.allowlist_external_dirs = {tmp_path}
    entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        entry, unique_id=testfile, data={CONF_FILE_PATH: testfile}
    )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    expect(bool(hass.data.get(DOMAIN))).to_be(False)
    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def cannot_access_file(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test that a missing file is caught."""
    entry.add_to_hass(hass)
    testfile = str(tmp_path.joinpath("file_not_exist.txt"))
    hass.config.allowlist_external_dirs = {tmp_path}
    hass.config_entries.async_update_entry(
        entry, unique_id=testfile, data={CONF_FILE_PATH: testfile}
    )

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def not_valid_path_to_file(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test that an invalid path is caught."""
    testfile = str(tmp_path.joinpath("file.txt"))
    await async_create_file(hass, testfile)
    entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        entry, unique_id=testfile, data={CONF_FILE_PATH: testfile}
    )

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
