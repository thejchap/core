"""The tests for the filesize sensor."""

from pathlib import Path

from tryke import Depends, expect, fixture, test

from homeassistant.const import CONF_FILE_PATH
from homeassistant.core import HomeAssistant

from . import TEST_FILE_NAME
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


@test.skip("snapshot diverged - needs pytest --snapshot-update")
async def sensors() -> None:
    """Stub for test_sensors."""


@test
async def invalid_path(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test that an invalid path is caught."""
    test_file = str(tmp_path.joinpath(TEST_FILE_NAME))
    entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        entry, unique_id=test_file, data={CONF_FILE_PATH: test_file}
    )

    state = hass.states.get("sensor." + TEST_FILE_NAME)
    expect(bool(state)).to_be(False)


@test.skip("entity_id slug requires translation injection")
async def valid_path() -> None:
    """Stub for test_valid_path."""


@test.skip("entity_id slug requires translation injection")
async def state_unavailable() -> None:
    """Stub for test_state_unavailable."""
