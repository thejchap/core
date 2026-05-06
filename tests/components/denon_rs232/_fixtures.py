"""Tryke fixtures for the Denon RS232 integration."""

from __future__ import annotations

from typing import Literal
from unittest.mock import AsyncMock

from denon_rs232 import (
    DenonReceiver,
    DigitalInputMode,
    InputSource,
    MainZoneState,
    ReceiverState,
    TunerBand,
    TunerMode,
    ZoneState,
)
from denon_rs232.models import MODELS
from tryke import Depends, fixture

from homeassistant.core import HomeAssistant

from . import MOCK_DEVICE, MOCK_MODEL

from tests.hass_fixtures import hass as hass_fixture

ZoneName = Literal["main", "zone_2", "zone_3"]


class MockState(ReceiverState):
    """Receiver state with helpers for zone-oriented tests."""

    def get_zone(self, zone: ZoneName) -> ZoneState:
        """Return the requested zone state."""
        if zone == "main":
            return self.main_zone
        return getattr(self, zone)


class MockReceiver(DenonReceiver):
    """Receiver test double built on the real receiver/player objects."""

    def __init__(self, state: MockState) -> None:
        """Initialize the mock receiver."""
        super().__init__(MOCK_DEVICE, model=MODELS[MOCK_MODEL])
        self._connected = True
        self._load_state(state)
        self._send_command = AsyncMock()
        self._query = AsyncMock()
        self.connect = AsyncMock(side_effect=self._mock_connect)
        self.query_state = AsyncMock()
        self.disconnect = AsyncMock(side_effect=self._mock_disconnect)

    async def _mock_connect(self) -> None:
        """Pretend to open the serial connection."""
        self._connected = True

    async def _mock_disconnect(self) -> None:
        """Pretend to close the serial connection."""
        self._connected = False
        self._notify_subscribers()

    def _load_state(self, state: MockState) -> None:
        """Swap in a new state object and rebind the live players to it."""
        self._state = state
        self.main._state = state.main_zone
        self.zone_2._state = state.zone_2
        self.zone_3._state = state.zone_3


def _default_state() -> MockState:
    """Return a ReceiverState with typical defaults."""
    return MockState(
        power=True,
        main_zone=MainZoneState(
            power=True,
            volume=-30.0,
            volume_min=-80,
            volume_max=10,
            mute=False,
            input_source=InputSource.CD,
            surround_mode="STEREO",
            digital_input=DigitalInputMode.AUTO,
            tuner_band=TunerBand.FM,
            tuner_mode=TunerMode.AUTO,
        ),
        zone_2=ZoneState(
            power=True,
            input_source=InputSource.TUNER,
            volume=-20.0,
        ),
        zone_3=ZoneState(
            power=False,
            input_source=InputSource.CD,
            volume=-35.0,
        ),
    )


@fixture
def mock_receiver() -> MockReceiver:
    """Create a mock DenonReceiver."""
    return MockReceiver(_default_state())


@fixture
def mock_usb_component(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Mock the USB component to prevent setup failures."""
    hass.config.components.add("usb")
