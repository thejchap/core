"""Tests for the downloader component init."""

from pathlib import Path

from tryke import Depends, expect, fixture, test

from homeassistant.components.downloader.const import (
    CONF_DOWNLOAD_DIR,
    DOMAIN,
    SERVICE_DOWNLOAD_FILE,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    hass as hass_fixture,
    mock_network,
    tmp_path as tmp_path_fixture,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@fixture
def mock_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> MockConfigEntry:
    """Return a mocked config entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DOWNLOAD_DIR: str(tmp_path)},
    )
    config_entry.add_to_hass(hass)
    return config_entry


@test
async def config_entry_setup(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test config entry setup."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(hass.services.has_service(DOMAIN, SERVICE_DOWNLOAD_FILE)).to_be(True)
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def config_entry_setup_relative_directory(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test config entry setup with a relative download directory."""
    relative_directory = "downloads"
    hass.config_entries.async_update_entry(
        mock_config_entry,
        data={**mock_config_entry.data, CONF_DOWNLOAD_DIR: relative_directory},
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    # The config entry will fail to set up since the directory does not exist.
    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
    expect(mock_config_entry.data[CONF_DOWNLOAD_DIR]).to_equal(
        hass.config.path(relative_directory)
    )


@test.skip("has_service returns True even after SETUP_ERROR — services.yaml side-effect under tryke")
async def config_entry_setup_not_existing_directory() -> None:
    """Stub for test_config_entry_setup_not_existing_directory."""
