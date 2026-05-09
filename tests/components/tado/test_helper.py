"""Helper method tests."""

from unittest.mock import MagicMock, patch

from PyTado.interface import Tado
from tryke import Depends, expect, fixture, test

from homeassistant.components.tado import CONF_REFRESH_TOKEN, TadoDataUpdateCoordinator
from homeassistant.components.tado.const import (
    CONST_OVERLAY_MANUAL,
    CONST_OVERLAY_TADO_DEFAULT,
    CONST_OVERLAY_TADO_MODE,
    CONST_OVERLAY_TIMER,
    DOMAIN,
)
from homeassistant.components.tado.helper import decide_duration, decide_overlay_mode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


def _make_entry(fallback: str) -> MockConfigEntry:
    return MockConfigEntry(
        version=2,
        domain=DOMAIN,
        title="Tado",
        data={
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
            CONF_REFRESH_TOKEN: "test-refresh",
        },
        options={
            "fallback": fallback,
        },
    )


def _dummy_tado_connector(
    hass: HomeAssistant, entry: ConfigEntry, tado: Tado
) -> TadoDataUpdateCoordinator:
    return TadoDataUpdateCoordinator(hass, entry, tado)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture so tryke resolves Depends() per the migration pattern."""


@test
async def overlay_mode_duration_set(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test overlay method selection when duration is set."""
    entry = _make_entry(CONST_OVERLAY_TADO_MODE)
    with patch(
        "homeassistant.components.tado.PyTado.interface.api.Tado.set_zone_overlay"
    ) as mock_set_zone_overlay:
        tado_mock = MagicMock(spec=Tado)
        tado_mock.set_zone_overlay = mock_set_zone_overlay
        coordinator = _dummy_tado_connector(hass=hass, entry=entry, tado=tado_mock)
        overlay_mode = decide_overlay_mode(
            coordinator=coordinator, duration=3600, zone_id=1
        )
        expect(overlay_mode).to_equal(CONST_OVERLAY_TIMER)


@test
async def overlay_mode_next_time_block_fallback(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test overlay method selection when duration is not set."""
    entry = _make_entry(CONST_OVERLAY_TADO_MODE)
    with patch(
        "homeassistant.components.tado.PyTado.interface.api.Tado.set_zone_overlay"
    ) as mock_set_zone_overlay:
        tado_mock = MagicMock(spec=Tado)
        tado_mock.set_zone_overlay = mock_set_zone_overlay
        coordinator = _dummy_tado_connector(hass=hass, entry=entry, tado=tado_mock)
        overlay_mode = decide_overlay_mode(
            coordinator=coordinator, duration=None, zone_id=1
        )
        expect(overlay_mode).to_equal(CONST_OVERLAY_TADO_MODE)


@test
async def overlay_mode_tado_default_fallback(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test overlay method selection when tado default is selected."""
    entry = _make_entry(CONST_OVERLAY_TADO_DEFAULT)
    zone_fallback = CONST_OVERLAY_MANUAL
    with patch(
        "homeassistant.components.tado.PyTado.interface.api.Tado.set_zone_overlay"
    ) as mock_set_zone_overlay:
        tado_mock = MagicMock(spec=Tado)
        tado_mock.set_zone_overlay = mock_set_zone_overlay
        coordinator = _dummy_tado_connector(hass=hass, entry=entry, tado=tado_mock)

        class MockZoneData:
            def __init__(self) -> None:
                self.default_overlay_termination_type = zone_fallback

        zone_id = 1

        zone_data = {"zone": {zone_id: MockZoneData()}}
        with patch.dict(coordinator.data, zone_data):
            overlay_mode = decide_overlay_mode(
                coordinator=coordinator, duration=None, zone_id=zone_id
            )
            expect(overlay_mode).to_equal(zone_fallback)


@test
async def duration_enabled_without_tado_default(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test duration decide method when overlay is timer and duration is set."""
    entry = _make_entry(CONST_OVERLAY_MANUAL)
    overlay = CONST_OVERLAY_TIMER
    expected_duration = 600
    with patch(
        "homeassistant.components.tado.PyTado.interface.api.Tado.set_zone_overlay"
    ) as mock_set_zone_overlay:
        tado_mock = MagicMock(spec=Tado)
        tado_mock.set_zone_overlay = mock_set_zone_overlay
        coordinator = _dummy_tado_connector(hass=hass, entry=entry, tado=tado_mock)
        duration = decide_duration(
            coordinator=coordinator,
            duration=expected_duration,
            overlay_mode=overlay,
            zone_id=0,
        )
        expect(duration).to_equal(expected_duration)


@test
async def duration_enabled_with_tado_default(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test overlay method selection when ended up with timer overlay and None duration."""
    entry = _make_entry(CONST_OVERLAY_TIMER)
    zone_fallback = CONST_OVERLAY_TIMER
    expected_duration = 45000
    with patch(
        "homeassistant.components.tado.PyTado.interface.api.Tado.set_zone_overlay"
    ) as mock_set_zone_overlay:
        tado_mock = MagicMock(spec=Tado)
        tado_mock.set_zone_overlay = mock_set_zone_overlay
        coordinator = _dummy_tado_connector(hass=hass, entry=entry, tado=tado_mock)

        class MockZoneData:
            def __init__(self) -> None:
                self.default_overlay_termination_duration = expected_duration

        zone_id = 1

        zone_data = {"zone": {zone_id: MockZoneData()}}
        with patch.dict(coordinator.data, zone_data):
            duration = decide_duration(
                coordinator=coordinator,
                duration=None,
                zone_id=zone_id,
                overlay_mode=zone_fallback,
            )
            expect(duration).to_equal(expected_duration)
