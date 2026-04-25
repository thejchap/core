"""Tryke fixtures for the Whirlpool integration."""

from collections.abc import Generator
from unittest import mock
from unittest.mock import MagicMock, Mock

from tryke import fixture
from whirlpool import (
    appliancesmanager,
    auth,
    dryer,
    oven,
    refrigerator,
    washer,
)
from whirlpool.backendselector import Brand, Region

from .conftest import get_aircon_mock
from .const import MOCK_SAID1, MOCK_SAID2


@fixture
def mock_auth_api() -> Generator[MagicMock]:
    """Set up Auth fixture."""
    with (
        mock.patch(
            "homeassistant.components.whirlpool.Auth", spec=auth.Auth
        ) as mock_auth,
        mock.patch(
            "homeassistant.components.whirlpool.config_flow.Auth", new=mock_auth
        ),
    ):
        mock_auth.return_value.is_access_token_valid.return_value = True
        yield mock_auth


def _make_washer_mock() -> Mock:
    m = Mock(spec=washer.Washer, said="said_washer")
    m.name = "Washer"
    m.appliance_info = Mock(
        data_model="washer", category="washer_dryer", model_number="12345"
    )
    m.get_online.return_value = True
    m.get_machine_state.return_value = washer.MachineState.RunningMainCycle
    m.get_door_open.return_value = False
    m.get_dispense_1_level.return_value = 3
    m.get_time_remaining.return_value = 3540
    m.get_cycle_status_filling.return_value = False
    m.get_cycle_status_rinsing.return_value = False
    m.get_cycle_status_sensing.return_value = False
    m.get_cycle_status_soaking.return_value = False
    m.get_cycle_status_spinning.return_value = False
    m.get_cycle_status_washing.return_value = False
    return m


def _make_dryer_mock() -> Mock:
    m = Mock(spec=dryer.Dryer, said="said_dryer")
    m.name = "Dryer"
    m.appliance_info = Mock(
        data_model="dryer", category="washer_dryer", model_number="12345"
    )
    m.get_online.return_value = True
    m.get_machine_state.return_value = dryer.MachineState.RunningMainCycle
    m.get_door_open.return_value = False
    m.get_time_remaining.return_value = 3540
    m.get_cycle_status_sensing.return_value = False
    return m


def _make_oven_single_mock() -> Mock:
    m = Mock(spec=oven.Oven, said="said_oven_single")
    m.name = "Single Cavity Oven"
    m.appliance_info = Mock(
        data_model="oven", category="oven", model_number="12345"
    )
    m.get_cavity_state.return_value = oven.CavityState.Standby
    m.get_cook_mode.return_value = oven.CookMode.Bake
    m.get_online.return_value = True
    m.get_oven_cavity_exists.side_effect = lambda cavity: cavity == oven.Cavity.Upper
    m.get_temp.return_value = 180
    m.get_target_temp.return_value = 200
    return m


def _make_oven_dual_mock() -> Mock:
    m = Mock(spec=oven.Oven, said="said_oven_dual")
    m.name = "Dual Cavity Oven"
    m.appliance_info = Mock(
        data_model="oven", category="oven", model_number="12345"
    )
    m.get_cavity_state.return_value = oven.CavityState.Standby
    m.get_cook_mode.return_value = oven.CookMode.Bake
    m.get_online.return_value = True
    m.get_oven_cavity_exists.side_effect = lambda cavity: cavity in (
        oven.Cavity.Upper,
        oven.Cavity.Lower,
    )
    m.get_temp.return_value = 180
    m.get_target_temp.return_value = 200
    return m


def _make_refrigerator_mock() -> Mock:
    m = Mock(spec=refrigerator.Refrigerator, said="said_refrigerator")
    m.name = "Beer fridge"
    m.appliance_info = Mock(
        data_model="refrigerator", category="refrigerator", model_number="12345"
    )
    m.get_offset_temp.return_value = 0
    return m


@fixture
def mock_appliances_manager_api() -> Generator[MagicMock]:
    """Set up AppliancesManager fixture."""
    aircon1 = get_aircon_mock(MOCK_SAID1)
    aircon2 = get_aircon_mock(MOCK_SAID2)
    washer_m = _make_washer_mock()
    dryer_m = _make_dryer_mock()
    oven_single = _make_oven_single_mock()
    oven_dual = _make_oven_dual_mock()
    refrigerator_m = _make_refrigerator_mock()

    with (
        mock.patch(
            "homeassistant.components.whirlpool.AppliancesManager",
            spec=appliancesmanager.AppliancesManager,
        ) as mock_manager,
        mock.patch(
            "homeassistant.components.whirlpool.config_flow.AppliancesManager",
            new=mock_manager,
        ),
    ):
        mock_manager.return_value.aircons = [aircon1, aircon2]
        mock_manager.return_value.washers = [washer_m]
        mock_manager.return_value.dryers = [dryer_m]
        mock_manager.return_value.ovens = [oven_single, oven_dual]
        mock_manager.return_value.refrigerators = [refrigerator_m]
        yield mock_manager


@fixture
def mock_backend_selector_api() -> Generator[MagicMock]:
    """Set up BackendSelector fixture."""
    with (
        mock.patch(
            "homeassistant.components.whirlpool.BackendSelector"
        ) as mock_backend_selector,
        mock.patch(
            "homeassistant.components.whirlpool.config_flow.BackendSelector",
            new=mock_backend_selector,
        ),
    ):
        yield mock_backend_selector


@fixture
def mock_whirlpool_setup_entry() -> Generator[MagicMock]:
    """Set up async_setup_entry fixture."""
    with mock.patch(
        "homeassistant.components.whirlpool.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


# We pick a single (region, brand) tuple for testing under tryke.
# Original used pytest parametrize(2 regions x 3 brands); selected EU + Whirlpool.
DEFAULT_REGION: tuple[str, Region] = ("EU", Region.EU)
DEFAULT_BRAND: tuple[str, Brand] = ("Whirlpool", Brand.Whirlpool)
