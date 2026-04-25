"""Tryke fixtures for Velux tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from pyvlx import (
    Blind,
    DualRollerShutter,
    ExteriorHeating,
    Light,
    OnOffLight,
    OnOffSwitch,
    Scene,
    Window,
)
from tryke import Depends, fixture

from homeassistant.components.velux import DOMAIN
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_PASSWORD

from tests.common import MockConfigEntry


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.velux.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        entry_id="test_entry_id",
        domain=DOMAIN,
        title="127.0.0.1",
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PASSWORD: "NotAStrongPassword",
        },
    )


@fixture
def mock_discovered_config_entry() -> MockConfigEntry:
    """Return the user config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="127.0.0.1",
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PASSWORD: "NotAStrongPassword",
            CONF_MAC: "64:61:84:00:ab:cd",
        },
        unique_id="VELUX_KLF_ABCD",
    )


@fixture
def mock_window() -> AsyncMock:
    """Create a mock Velux window with a rain sensor."""
    window = AsyncMock(spec=Window, autospec=True)
    window.name = "Test Window"
    window.rain_sensor = True
    window.serial_number = "123456789"
    window.get_limitation_min.return_value = MagicMock(position_percent=0)
    window.device_updated_cbs = []
    window.is_opening = False
    window.is_closing = False
    window.position = MagicMock(position_percent=30, closed=False)
    window.wink = AsyncMock()
    window.pyvlx = MagicMock()
    return window


@fixture
def mock_dual_roller_shutter() -> AsyncMock:
    """Create a mock Velux dual roller shutter."""
    cover = AsyncMock(spec=DualRollerShutter, autospec=True)
    cover.name = "Test Dual Roller Shutter"
    cover.serial_number = "987654321"
    cover.is_opening = False
    cover.is_closing = False
    cover.position_upper_curtain = MagicMock(position_percent=30, closed=False)
    cover.position_lower_curtain = MagicMock(position_percent=30, closed=False)
    cover.position = MagicMock(position_percent=30, closed=False)
    cover.pyvlx = MagicMock()
    return cover


@fixture
def mock_blind() -> AsyncMock:
    """Create a mock Velux blind (cover with tilt)."""
    blind = AsyncMock(spec=Blind, autospec=True)
    blind.name = "Test Blind"
    blind.serial_number = "4711"
    blind.position = MagicMock(position_percent=40, closed=False)
    blind.is_opening = False
    blind.is_closing = False
    blind.orientation = MagicMock(position_percent=25)
    blind.open_orientation = AsyncMock()
    blind.close_orientation = AsyncMock()
    blind.stop_orientation = AsyncMock()
    blind.set_orientation = AsyncMock()
    blind.pyvlx = MagicMock()
    return blind


@fixture
def mock_light() -> AsyncMock:
    """Create a mock Velux light."""
    light = AsyncMock(spec=Light, autospec=True)
    light.name = "Test Light"
    light.serial_number = "0815"
    light.intensity = MagicMock()
    light.pyvlx = MagicMock()
    return light


@fixture
def mock_onoff_light() -> AsyncMock:
    """Create a mock Velux on/off light."""
    light = AsyncMock(spec=OnOffLight, autospec=True)
    light.name = "Test On Off Light"
    light.serial_number = "0816"
    light.intensity = MagicMock()
    light.pyvlx = MagicMock()
    return light


@fixture
def mock_exterior_heating() -> AsyncMock:
    """Create a mock Velux exterior heating device."""
    exterior_heating = AsyncMock(spec=ExteriorHeating, autospec=True)
    exterior_heating.name = "Test Exterior Heating"
    exterior_heating.serial_number = "1984"
    exterior_heating.intensity = MagicMock(intensity_percent=33)
    exterior_heating.pyvlx = MagicMock()
    return exterior_heating


@fixture
def mock_onoff_switch() -> AsyncMock:
    """Create a mock Velux on/off switch."""
    switch = AsyncMock(spec=OnOffSwitch, autospec=True)
    switch.name = "Test On Off Switch"
    switch.serial_number = "0817"
    switch.is_on.return_value = False
    switch.is_off.return_value = True
    switch.pyvlx = MagicMock()
    return switch


@fixture
def mock_scene() -> AsyncMock:
    """Create a mock Velux scene."""
    scene = AsyncMock(spec=Scene, autospec=True)
    scene.name = "Test Scene"
    scene.scene_id = "1234"
    scene.scene = AsyncMock()
    return scene


@fixture
def mock_pyvlx(
    scene: AsyncMock = Depends(mock_scene),
    light: AsyncMock = Depends(mock_light),
    onoff_light: AsyncMock = Depends(mock_onoff_light),
    onoff_switch: AsyncMock = Depends(mock_onoff_switch),
    window: AsyncMock = Depends(mock_window),
    blind: AsyncMock = Depends(mock_blind),
    exterior_heating: AsyncMock = Depends(mock_exterior_heating),
    dual_roller_shutter: AsyncMock = Depends(mock_dual_roller_shutter),
) -> Generator[MagicMock]:
    """Create the library mock and patch PyVLX in both component and config_flow."""
    pyvlx = MagicMock()
    pyvlx.nodes = [
        dual_roller_shutter,
        light,
        onoff_light,
        onoff_switch,
        blind,
        window,
        exterior_heating,
    ]
    pyvlx.scenes = [scene]
    pyvlx.load_scenes = AsyncMock()
    pyvlx.load_nodes = AsyncMock()
    pyvlx.connect = AsyncMock()
    pyvlx.disconnect = AsyncMock()

    with (
        patch("homeassistant.components.velux.PyVLX", return_value=pyvlx),
        patch(
            "homeassistant.components.velux.config_flow.PyVLX", return_value=pyvlx
        ),
    ):
        yield pyvlx
