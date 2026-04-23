"""Tryke fixtures for niko_home_control tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from nhc.cover import NHCCover
from nhc.light import NHCLight
from nhc.scene import NHCScene
from nhc.thermostat import NHCThermostat
from tryke import Depends, fixture

from homeassistant.components.niko_home_control.const import DOMAIN
from homeassistant.const import CONF_HOST

from tests.common import MockConfigEntry


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override integration setup."""
    with patch(
        "homeassistant.components.niko_home_control.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock


@fixture
def light() -> NHCLight:
    """Return a light mock."""
    mock = AsyncMock(spec=NHCLight)
    mock.id = 1
    mock.type = 1
    mock.is_dimmable = False
    mock.name = "light"
    mock.suggested_area = "room"
    mock.state = 100
    return mock


@fixture
def dimmable_light() -> NHCLight:
    """Return a dimmable light mock."""
    mock = AsyncMock(spec=NHCLight)
    mock.id = 2
    mock.type = 2
    mock.is_dimmable = True
    mock.name = "dimmable light"
    mock.suggested_area = "room"
    mock.state = 100
    return mock


@fixture
def cover() -> NHCCover:
    """Return a cover mock."""
    mock = AsyncMock(spec=NHCCover)
    mock.id = 3
    mock.type = 4
    mock.name = "cover"
    mock.suggested_area = "room"
    mock.state = 100
    return mock


@fixture
def climate() -> NHCThermostat:
    """Return a thermostat mock."""
    mock = AsyncMock(spec=NHCThermostat)
    mock.id = 5
    mock.name = "thermostat"
    mock.suggested_area = "room"
    mock.state = 0
    mock.measured = 180
    mock.setpoint = 200
    mock.overrule = 0
    mock.overruletime = 0
    mock.ecosave = 0
    return mock


@fixture
def scene() -> NHCScene:
    """Return a scene mock."""
    mock = AsyncMock(spec=NHCScene)
    mock.id = 4
    mock.type = 0
    mock.name = "scene"
    mock.suggested_area = "room"
    mock.state = 0
    return mock


@fixture
def mock_niko_home_control_connection(
    light_: NHCLight = Depends(light),
    dimmable_light_: NHCLight = Depends(dimmable_light),
    cover_: NHCCover = Depends(cover),
    climate_: NHCThermostat = Depends(climate),
    scene_: NHCScene = Depends(scene),
) -> Generator[AsyncMock]:
    """Mock a NHC client."""
    with (
        patch(
            "homeassistant.components.niko_home_control.NHCController",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.niko_home_control.config_flow.NHCController",
            new=mock_client,
        ),
    ):
        client = mock_client.return_value
        client.lights = [light_, dimmable_light_]
        client.covers = [cover_]
        client.thermostats = {"thermostat-5": climate_}
        client.scenes = [scene_]
        client.connect = AsyncMock(return_value=True)
        yield client


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Niko Home Control",
        data={CONF_HOST: "192.168.0.123"},
        entry_id="01JFN93M7KRA38V5AMPCJ2JYYV",
    )
