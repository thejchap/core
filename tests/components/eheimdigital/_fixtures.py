"""Tryke fixtures for the EHEIM Digital integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from eheimdigital.classic_led_ctrl import EheimDigitalClassicLEDControl
from eheimdigital.classic_vario import EheimDigitalClassicVario
from eheimdigital.filter import EheimDigitalFilter
from eheimdigital.heater import EheimDigitalHeater
from eheimdigital.hub import EheimDigitalHub
from eheimdigital.reeflex import EheimDigitalReeflexUV
from eheimdigital.types import (
    AcclimatePacket,
    CCVPacket,
    ClassicVarioDataPacket,
    ClockPacket,
    CloudPacket,
    FilterDataPacket,
    MoonPacket,
    ReeflexDataPacket,
    UsrDtaPacket,
)
from tryke import Depends, fixture

from homeassistant.components.eheimdigital.const import DOMAIN
from homeassistant.const import CONF_HOST

from tests.common import MockConfigEntry, load_json_object_fixture


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "eheimdigital"}, unique_id="00:00:00:00:00:01"
    )


@fixture
def classic_led_ctrl_mock() -> MagicMock:
    """Mock a classicLEDcontrol device."""
    classic_led_ctrl = EheimDigitalClassicLEDControl(
        MagicMock(spec=EheimDigitalHub),
        UsrDtaPacket(load_json_object_fixture("classic_led_ctrl/usrdta.json", DOMAIN)),
    )
    classic_led_ctrl.ccv = CCVPacket(
        load_json_object_fixture("classic_led_ctrl/ccv.json", DOMAIN)
    )
    classic_led_ctrl.moon = MoonPacket(
        load_json_object_fixture("classic_led_ctrl/moon.json", DOMAIN)
    )
    classic_led_ctrl.acclimate = AcclimatePacket(
        load_json_object_fixture("classic_led_ctrl/acclimate.json", DOMAIN)
    )
    classic_led_ctrl.cloud = CloudPacket(
        load_json_object_fixture("classic_led_ctrl/cloud.json", DOMAIN)
    )
    classic_led_ctrl.clock = ClockPacket(
        load_json_object_fixture("classic_led_ctrl/clock.json", DOMAIN)
    )
    return classic_led_ctrl


@fixture
def heater_mock() -> MagicMock:
    """Mock a Heater device."""
    heater = EheimDigitalHeater(
        MagicMock(spec=EheimDigitalHub),
        load_json_object_fixture("heater/usrdta.json", DOMAIN),
    )
    heater.heater_data = load_json_object_fixture("heater/heater_data.json", DOMAIN)
    return heater


@fixture
def classic_vario_mock() -> MagicMock:
    """Mock a classicVARIO device."""
    classic_vario = EheimDigitalClassicVario(
        MagicMock(spec=EheimDigitalHub),
        UsrDtaPacket(load_json_object_fixture("classic_vario/usrdta.json", DOMAIN)),
    )
    classic_vario.classic_vario_data = ClassicVarioDataPacket(
        load_json_object_fixture("classic_vario/classic_vario_data.json", DOMAIN)
    )
    return classic_vario


@fixture
def filter_mock() -> MagicMock:
    """Mock a filter device."""
    eheim_filter = EheimDigitalFilter(
        MagicMock(spec=EheimDigitalHub),
        UsrDtaPacket(load_json_object_fixture("filter/usrdta.json", DOMAIN)),
    )
    eheim_filter.filter_data = FilterDataPacket(
        load_json_object_fixture("filter/filter_data.json", DOMAIN)
    )
    return eheim_filter


@fixture
def reeflex_mock() -> MagicMock:
    """Mock a reeflex device."""
    eheim_reeflex = EheimDigitalReeflexUV(
        MagicMock(spec=EheimDigitalHub),
        UsrDtaPacket(load_json_object_fixture("reeflex/usrdta.json", DOMAIN)),
    )
    eheim_reeflex.reeflex_data = ReeflexDataPacket(
        load_json_object_fixture("reeflex/reeflex_data.json", DOMAIN)
    )
    return eheim_reeflex


@fixture
def eheimdigital_hub_mock(
    classic_led_ctrl: MagicMock = Depends(classic_led_ctrl_mock),
    heater: MagicMock = Depends(heater_mock),
    classic_vario: MagicMock = Depends(classic_vario_mock),
    eheim_filter: MagicMock = Depends(filter_mock),
    reeflex: MagicMock = Depends(reeflex_mock),
) -> Generator[AsyncMock]:
    """Mock eheimdigital hub."""
    with (
        patch(
            "homeassistant.components.eheimdigital.coordinator.EheimDigitalHub",
            spec=EheimDigitalHub,
        ) as eheimdigital_hub_mock,
        patch(
            "homeassistant.components.eheimdigital.config_flow.EheimDigitalHub",
            new=eheimdigital_hub_mock,
        ),
    ):
        eheimdigital_hub_mock.return_value.devices = {
            "00:00:00:00:00:01": classic_led_ctrl,
            "00:00:00:00:00:02": heater,
            "00:00:00:00:00:03": classic_vario,
            "00:00:00:00:00:04": eheim_filter,
            "00:00:00:00:00:05": reeflex,
        }
        eheimdigital_hub_mock.return_value.main = classic_led_ctrl
        yield eheimdigital_hub_mock
