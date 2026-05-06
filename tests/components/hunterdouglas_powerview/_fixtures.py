"""Tryke fixtures for the Hunter Douglas Powerview integration."""

from collections.abc import Generator
from contextlib import ExitStack, contextmanager
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

from aiopvapi.resources.shade import ShadePosition
from tryke import fixture

from homeassistant.components.hunterdouglas_powerview.const import DOMAIN

from tests.common import load_json_object_fixture, load_json_value_fixture

_DEVICE_FIXTURES = {
    1: ("gen1/userdata.json", "gen1/userdata.json", "gen1/fwversion.json"),
    2: ("gen2/userdata.json", "gen2/userdata.json", "gen2/fwversion.json"),
    3: ("gen3/gateway/primary.json", "gen3/home/home.json", "gen3/gateway/info.json"),
}

_RESOURCE_FIXTURES = {
    1: ("gen1/rooms.json", "gen1/scenes.json", "gen1/shades.json"),
    2: ("gen2/rooms.json", "gen2/scenes.json", "gen2/shades.json"),
    3: ("gen3/home/rooms.json", "gen3/home/scenes.json", "gen3/home/shades.json"),
}


@contextmanager
def hub_patches(api_version: int) -> Generator[None]:
    """Patch all Hub-related methods for a given API version."""
    device_json, home_json, firmware_json = _DEVICE_FIXTURES[api_version]
    rooms_json, scenes_json, shades_json = _RESOURCE_FIXTURES[api_version]
    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "homeassistant.components.hunterdouglas_powerview.util.Hub.request_raw_data",
                return_value=load_json_object_fixture(device_json, DOMAIN),
            )
        )
        stack.enter_context(
            patch(
                "homeassistant.components.hunterdouglas_powerview.util.Hub.request_home_data",
                return_value=load_json_object_fixture(home_json, DOMAIN),
            )
        )
        stack.enter_context(
            patch(
                "homeassistant.components.hunterdouglas_powerview.util.Hub.request_raw_firmware",
                return_value=load_json_object_fixture(firmware_json, DOMAIN),
            )
        )
        stack.enter_context(
            patch(
                "homeassistant.components.hunterdouglas_powerview.Rooms.get_resources",
                return_value=load_json_value_fixture(rooms_json, DOMAIN),
            )
        )
        stack.enter_context(
            patch(
                "homeassistant.components.hunterdouglas_powerview.Scenes.get_resources",
                return_value=load_json_value_fixture(scenes_json, DOMAIN),
            )
        )
        stack.enter_context(
            patch(
                "homeassistant.components.hunterdouglas_powerview.Shades.get_resources",
                return_value=load_json_value_fixture(shades_json, DOMAIN),
            )
        )
        stack.enter_context(
            patch(
                "homeassistant.components.hunterdouglas_powerview.cover.BaseShade.refresh",
            )
        )
        stack.enter_context(
            patch(
                "homeassistant.components.hunterdouglas_powerview.cover.BaseShade.current_position",
                new_callable=PropertyMock,
                return_value=ShadePosition(primary=0, secondary=0, tilt=0, velocity=0),
            )
        )
        yield


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.hunterdouglas_powerview.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry
