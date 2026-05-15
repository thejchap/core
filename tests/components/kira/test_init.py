"""The tests for Kira."""

from collections.abc import Generator
import os
from pathlib import Path
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import kira
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture, mock_network, tmp_path

TEST_CONFIG = {
    kira.DOMAIN: {
        "sensors": [
            {"name": "test_sensor", "host": "127.0.0.1", "port": 34293},
            {"name": "second_sensor", "port": 29847},
        ],
        "remotes": [
            {"host": "127.0.0.1", "port": 34293},
            {"name": "one_more", "host": "127.0.0.1", "port": 29847},
        ],
    }
}

KIRA_CODES = """
- name: test
  code: "K 00FF"
- invalid: not_a_real_code
"""


@fixture
def setup_comp() -> Generator[None]:
    """Set up things to be run when tests are started."""
    with patch("homeassistant.components.kira.pykira.KiraReceiver"):
        yield


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: None = Depends(setup_comp),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def kira_empty_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Kira component should load a default sensor."""
    await async_setup_component(hass, kira.DOMAIN, {kira.DOMAIN: {}})
    expect(len(hass.data[kira.DOMAIN]["sensor"])).to_equal(1)


@test
async def kira_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure platforms are loaded correctly."""
    await async_setup_component(hass, kira.DOMAIN, TEST_CONFIG)
    await hass.async_block_till_done()

    expect(len(hass.data[kira.DOMAIN]["sensor"])).to_equal(2)
    expect(sorted(hass.data[kira.DOMAIN]["sensor"].keys())).to_equal(
        ["kira", "kira_1"]
    )
    expect(len(hass.data[kira.DOMAIN]["remote"])).to_equal(2)
    expect(sorted(hass.data[kira.DOMAIN]["remote"].keys())).to_equal(
        ["kira", "kira_1"]
    )


@test
async def kira_creates_codes(
    _trigger: None = Depends(_trigger_executor),
    work_dir: Path = Depends(tmp_path),
) -> None:
    """Kira module should create codes file if missing."""
    code_path = os.path.join(work_dir, "codes.yaml")
    kira.load_codes(code_path)
    expect(os.path.exists(code_path)).to_be(True)


@test
async def load_codes(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    work_dir: Path = Depends(tmp_path),
) -> None:
    """Kira should ignore invalid codes."""
    code_path = os.path.join(work_dir, "codes.yaml")
    await hass.async_add_executor_job(Path(code_path).write_text, KIRA_CODES)
    res = kira.load_codes(code_path)
    expect(len(res)).to_equal(1)
