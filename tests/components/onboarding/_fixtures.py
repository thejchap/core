"""Tryke fixtures for the onboarding tests."""

from collections.abc import AsyncGenerator, Generator
from dataclasses import replace
import os
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import register_auth_provider
from tests.components.hassio._fixtures import (
    homeassistant_info as homeassistant_info_fixture,
    host_info as host_info_fixture,
    ingress_panels as ingress_panels_fixture,
    network_info as network_info_fixture,
    os_info as os_info_fixture,
    resolution_info as resolution_info_fixture,
    store_info as store_info_fixture,
    supervisor_info as supervisor_info_fixture,
    supervisor_is_connected as supervisor_is_connected_fixture,
    supervisor_root_info as supervisor_root_info_fixture,
)
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def auth_active(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Ensure auth is always active."""
    await register_auth_provider(hass, {"type": "homeassistant"})


@fixture
def mock_default_integrations() -> Generator[None]:
    """Mock the default integrations set up during onboarding."""
    with (
        patch("homeassistant.components.rpi_power.config_flow.new_under_voltage"),
        patch("homeassistant.components.rpi_power.binary_sensor.new_under_voltage"),
        patch("homeassistant.components.met.async_setup_entry", return_value=True),
        patch(
            "homeassistant.components.radio_browser.async_setup_entry",
            return_value=True,
        ),
        patch(
            "homeassistant.components.shopping_list.async_setup_entry",
            return_value=True,
        ),
    ):
        yield


@fixture
async def mock_supervisor(
    hass: HomeAssistant = Depends(hass_fixture),
    store_info: AsyncMock = Depends(store_info_fixture),
    supervisor_is_connected: AsyncMock = Depends(supervisor_is_connected_fixture),
    resolution_info: AsyncMock = Depends(resolution_info_fixture),
    supervisor_root_info: AsyncMock = Depends(supervisor_root_info_fixture),
    host_info: AsyncMock = Depends(host_info_fixture),
    supervisor_info: AsyncMock = Depends(supervisor_info_fixture),
    network_info: AsyncMock = Depends(network_info_fixture),
    os_info: AsyncMock = Depends(os_info_fixture),
    ingress_panels: AsyncMock = Depends(ingress_panels_fixture),
) -> AsyncGenerator[None]:
    """Mock supervisor."""
    supervisor_info.return_value = replace(
        supervisor_info.return_value, diagnostics=True
    )
    with (
        patch.dict(os.environ, {"SUPERVISOR": "127.0.0.1"}),
        patch.dict(os.environ, {"SUPERVISOR_TOKEN": "123456"}),
    ):
        yield


@fixture
async def no_rpi(
    hass: HomeAssistant = Depends(hass_fixture),
    homeassistant_info: AsyncMock = Depends(homeassistant_info_fixture),
    _mock_supervisor: None = Depends(mock_supervisor),
) -> None:
    """Mock core info with a non-RPi machine."""
    homeassistant_info.return_value = replace(
        homeassistant_info.return_value, machine="odroid-n2"
    )
    assert await async_setup_component(hass, "hassio", {})
    await hass.async_block_till_done()
