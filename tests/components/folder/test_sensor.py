"""The tests for the folder sensor."""

import os

from tryke import Depends, expect, fixture, test

from homeassistant.components.folder.sensor import CONF_FOLDER_PATHS
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass

CWD = os.path.join(os.path.dirname(__file__))
TEST_FOLDER = "test_folder"
TEST_DIR = os.path.join(CWD, TEST_FOLDER)
TEST_TXT = "mock_test_folder.txt"
TEST_FILE = os.path.join(TEST_DIR, TEST_TXT)


def create_file(path: str) -> None:
    """Create a test file."""
    with open(path, "w", encoding="utf8") as test_file:
        test_file.write("test")


def remove_test_file() -> None:
    """Remove test file."""
    if os.path.isfile(TEST_FILE):
        os.remove(TEST_FILE)
        os.rmdir(TEST_DIR)


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def invalid_path(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that an invalid path is caught."""
    config = {"sensor": {"platform": "folder", CONF_FOLDER_PATHS: "invalid_path"}}
    result = await async_setup_component(hass, "sensor", config)
    expect(result).to_be(True)
    expect(len(hass.states.async_entity_ids("sensor"))).to_equal(0)


@test
async def valid_path(hass: HomeAssistant = Depends(hass)) -> None:
    """Test for a valid path."""
    if not os.path.isdir(TEST_DIR):
        os.mkdir(TEST_DIR)
    create_file(TEST_FILE)

    hass.config.allowlist_external_dirs = {TEST_DIR}
    config = {"sensor": {"platform": "folder", CONF_FOLDER_PATHS: TEST_DIR}}
    result = await async_setup_component(hass, "sensor", config)
    expect(result).to_be(True)
    await hass.async_block_till_done()
    expect(len(hass.states.async_entity_ids())).to_equal(1)
    state = hass.states.get("sensor.test_folder")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("0.0")
    expect(state.attributes.get("number_of_files")).to_equal(1)

    remove_test_file()
