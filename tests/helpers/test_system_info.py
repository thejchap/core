"""Tests for the system info helper."""

import json
import os
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import hassio
from homeassistant.const import __version__ as current_version
from homeassistant.core import HomeAssistant
from homeassistant.helpers.hassio import is_hassio
from homeassistant.helpers.system_info import async_get_system_info

from tests.hass_fixtures import LogCapture, caplog, hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def get_system_info(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the get system info."""
    info = await async_get_system_info(hass)
    expect(isinstance(info, dict)).to_be(True)
    expect(info["version"]).to_equal(current_version)
    expect(info["user"]).not_.to_be_none()
    expect(json.dumps(info) is not None).to_be(True)


@test
async def get_system_info_supervisor_not_available(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test the get system info when supervisor is not available."""
    hass.config.components.add("hassio")
    expect(is_hassio(hass)).to_be(True)
    with (
        patch("platform.system", return_value="Linux"),
        patch("homeassistant.helpers.system_info.is_docker_env", return_value=True),
        patch("homeassistant.helpers.system_info.is_official_image", return_value=True),
        patch("homeassistant.helpers.hassio.is_hassio", return_value=True),
        patch.object(hassio, "get_info", return_value=None),
        patch("homeassistant.helpers.system_info.cached_get_user", return_value="root"),
    ):
        info = await async_get_system_info(hass)
        expect(isinstance(info, dict)).to_be(True)
        expect(info["version"]).to_equal(current_version)
        expect(info["user"]).not_.to_be_none()
        expect(json.dumps(info) is not None).to_be(True)
        expect(info["installation_type"]).to_equal("Home Assistant Supervised")
        expect("No Home Assistant Supervisor info available" in caplog.text).to_be(True)


@test
async def get_system_info_supervisor_not_loaded(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test the get system info when supervisor is not loaded."""
    expect(is_hassio(hass)).to_be(False)
    with (
        patch("platform.system", return_value="Linux"),
        patch("homeassistant.helpers.system_info.is_docker_env", return_value=True),
        patch("homeassistant.helpers.system_info.is_official_image", return_value=True),
        patch.object(hassio, "get_info", return_value=None),
        patch.dict(os.environ, {"SUPERVISOR": "127.0.0.1"}),
    ):
        info = await async_get_system_info(hass)
        expect(isinstance(info, dict)).to_be(True)
        expect(info["version"]).to_equal(current_version)
        expect(info["user"]).not_.to_be_none()
        expect(json.dumps(info) is not None).to_be(True)
        expect(info["installation_type"]).to_equal("Unsupported Third Party Container")


@test.cases(
    test.case(
        "True-True-True-root-Home Assistant Container",
        is_docker_env=True,
        is_official=True,
        is_venv=True,
        user="root",
        expected_installation_type="Home Assistant Container",
    ),
    test.case(
        "True-True-True-user-Unsupported Third Party Container",
        is_docker_env=True,
        is_official=True,
        is_venv=True,
        user="user",
        expected_installation_type="Unsupported Third Party Container",
    ),
    test.case(
        "True-False-True-root-Unsupported Third Party Container",
        is_docker_env=True,
        is_official=False,
        is_venv=True,
        user="root",
        expected_installation_type="Unsupported Third Party Container",
    ),
    test.case(
        "True-False-True-user-Unsupported Third Party Container",
        is_docker_env=True,
        is_official=False,
        is_venv=True,
        user="user",
        expected_installation_type="Unsupported Third Party Container",
    ),
    test.case(
        "True-True-False-root-Home Assistant Container",
        is_docker_env=True,
        is_official=True,
        is_venv=False,
        user="root",
        expected_installation_type="Home Assistant Container",
    ),
    test.case(
        "True-True-False-user-Unsupported Third Party Container",
        is_docker_env=True,
        is_official=True,
        is_venv=False,
        user="user",
        expected_installation_type="Unsupported Third Party Container",
    ),
    test.case(
        "True-False-False-root-Unsupported Third Party Container",
        is_docker_env=True,
        is_official=False,
        is_venv=False,
        user="root",
        expected_installation_type="Unsupported Third Party Container",
    ),
    test.case(
        "True-False-False-user-Unsupported Third Party Container",
        is_docker_env=True,
        is_official=False,
        is_venv=False,
        user="user",
        expected_installation_type="Unsupported Third Party Container",
    ),
    test.case(
        "False-True-True-root-Home Assistant Core",
        is_docker_env=False,
        is_official=True,
        is_venv=True,
        user="root",
        expected_installation_type="Home Assistant Core",
    ),
    test.case(
        "False-True-True-user-Home Assistant Core",
        is_docker_env=False,
        is_official=True,
        is_venv=True,
        user="user",
        expected_installation_type="Home Assistant Core",
    ),
    test.case(
        "False-False-True-root-Home Assistant Core",
        is_docker_env=False,
        is_official=False,
        is_venv=True,
        user="root",
        expected_installation_type="Home Assistant Core",
    ),
    test.case(
        "False-False-True-user-Home Assistant Core",
        is_docker_env=False,
        is_official=False,
        is_venv=True,
        user="user",
        expected_installation_type="Home Assistant Core",
    ),
    test.case(
        "False-True-False-root-Unknown",
        is_docker_env=False,
        is_official=True,
        is_venv=False,
        user="root",
        expected_installation_type="Unknown",
    ),
    test.case(
        "False-True-False-user-Unknown",
        is_docker_env=False,
        is_official=True,
        is_venv=False,
        user="user",
        expected_installation_type="Unknown",
    ),
    test.case(
        "False-False-False-root-Unknown",
        is_docker_env=False,
        is_official=False,
        is_venv=False,
        user="root",
        expected_installation_type="Unknown",
    ),
    test.case(
        "False-False-False-user-Unknown",
        is_docker_env=False,
        is_official=False,
        is_venv=False,
        user="user",
        expected_installation_type="Unknown",
    ),
)
async def non_hassio_installation_type(
    is_docker_env: bool,
    is_official: bool,
    is_venv: bool,
    user: str,
    expected_installation_type: str,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test non-Hass.io installation types."""
    expect(is_hassio(hass)).to_be(False)
    with (
        patch("platform.system", return_value="Linux"),
        patch(
            "homeassistant.helpers.system_info.is_docker_env",
            return_value=is_docker_env,
        ),
        patch(
            "homeassistant.helpers.system_info.is_official_image",
            return_value=is_official,
        ),
        patch(
            "homeassistant.helpers.system_info.is_virtual_env",
            return_value=is_venv,
        ),
        patch("homeassistant.helpers.system_info.cached_get_user", return_value=user),
        patch(
            "homeassistant.helpers.system_info.async_get_container_arch",
            return_value="aarch64",
        ),
    ):
        info = await async_get_system_info(hass)
        expect(info["installation_type"]).to_equal(expected_installation_type)


@test.cases(
    test.case("KeyError", error=KeyError),
    test.case("OSError", error=OSError),
)
async def getuser_oserror(
    error: type[Exception],
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test getuser oserror."""
    with patch("homeassistant.helpers.system_info.cached_get_user", side_effect=error):
        info = await async_get_system_info(hass)
        expect(info["user"]).to_be_none()
