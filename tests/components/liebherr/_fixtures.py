"""Tryke fixtures for Liebherr tests."""

from __future__ import annotations

from collections.abc import Generator
import copy
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from pyliebherrhomeapi import (
    BioFreshPlusControl,
    BioFreshPlusMode,
    Device,
    DeviceState,
    DeviceType,
    HydroBreezeControl,
    HydroBreezeMode,
    IceMakerControl,
    IceMakerMode,
    PresentationLightControl,
    TemperatureControl,
    TemperatureUnit,
    ToggleControl,
    ZonePosition,
)
from tryke import fixture

from homeassistant.components.liebherr.const import DOMAIN
from homeassistant.const import CONF_API_KEY

from tests.common import MockConfigEntry

MOCK_DEVICE = Device(
    device_id="test_device_id",
    nickname="Test Fridge",
    device_type=DeviceType.COMBI,
    device_name="CBNes1234",
)

MOCK_DEVICE_STATE = DeviceState(
    device=MOCK_DEVICE,
    controls=[
        TemperatureControl(
            zone_id=1,
            zone_position=ZonePosition.TOP,
            name="Fridge",
            type="fridge",
            value=5,
            target=4,
            min=2,
            max=8,
            unit=TemperatureUnit.CELSIUS,
        ),
        TemperatureControl(
            zone_id=2,
            zone_position=ZonePosition.BOTTOM,
            name="Freezer",
            type="freezer",
            value=-18,
            target=-18,
            min=-24,
            max=-16,
            unit=TemperatureUnit.CELSIUS,
        ),
        ToggleControl(
            name="supercool",
            type="ToggleControl",
            zone_id=1,
            zone_position=ZonePosition.TOP,
            value=False,
        ),
        ToggleControl(
            name="superfrost",
            type="ToggleControl",
            zone_id=2,
            zone_position=ZonePosition.BOTTOM,
            value=True,
        ),
        ToggleControl(
            name="partymode",
            type="ToggleControl",
            zone_id=None,
            zone_position=None,
            value=False,
        ),
        ToggleControl(
            name="nightmode",
            type="ToggleControl",
            zone_id=None,
            zone_position=None,
            value=True,
        ),
        IceMakerControl(
            name="icemaker",
            type="IceMakerControl",
            zone_id=2,
            zone_position=ZonePosition.BOTTOM,
            ice_maker_mode=IceMakerMode.OFF,
            has_max_ice=True,
        ),
        HydroBreezeControl(
            name="hydrobreeze",
            type="HydroBreezeControl",
            zone_id=1,
            current_mode=HydroBreezeMode.LOW,
        ),
        BioFreshPlusControl(
            name="biofreshplus",
            type="BioFreshPlusControl",
            zone_id=1,
            current_mode=BioFreshPlusMode.ZERO_ZERO,
            supported_modes=[
                BioFreshPlusMode.ZERO_ZERO,
                BioFreshPlusMode.ZERO_MINUS_TWO,
                BioFreshPlusMode.MINUS_TWO_MINUS_TWO,
                BioFreshPlusMode.MINUS_TWO_ZERO,
            ],
        ),
        PresentationLightControl(
            name="presentationlight",
            type="PresentationLightControl",
            value=3,
            max=5,
        ),
    ],
)


@fixture
def patch_refresh_delay() -> Generator[None]:
    """Patch REFRESH_DELAY to 0 to avoid delays in tests."""
    with patch(
        "homeassistant.components.liebherr.entity.REFRESH_DELAY",
        timedelta(seconds=0),
    ):
        yield


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.liebherr.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "test-api-key"},
        title="Liebherr",
    )


@fixture
def mock_liebherr_client() -> Generator[MagicMock]:
    """Return a mocked Liebherr client."""
    with (
        patch(
            "homeassistant.components.liebherr.LiebherrClient",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.liebherr.config_flow.LiebherrClient",
            new=mock_client,
        ),
    ):
        client = mock_client.return_value
        client.get_devices.return_value = [MOCK_DEVICE]
        client.get_device_state.side_effect = lambda *a, **kw: copy.deepcopy(
            MOCK_DEVICE_STATE
        )
        client.set_temperature = AsyncMock()
        client.set_super_cool = AsyncMock()
        client.set_super_frost = AsyncMock()
        client.set_party_mode = AsyncMock()
        client.set_night_mode = AsyncMock()
        client.set_ice_maker = AsyncMock()
        client.set_hydro_breeze = AsyncMock()
        client.set_bio_fresh_plus = AsyncMock()
        client.set_presentation_light = AsyncMock()
        yield client
