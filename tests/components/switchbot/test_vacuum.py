"""Tests for switchbot vacuum."""

from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.components.vacuum import (
    DOMAIN as VACUUM_DOMAIN,
    SERVICE_RETURN_TO_BASE,
    SERVICE_START,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

from . import (
    K10_POR_COMBO_VACUUM_SERVICE_INFO,
    K10_PRO_VACUUM_SERVICE_INFO,
    K10_VACUUM_SERVICE_INFO,
    K11_PLUS_VACUUM_SERVICE_INFO,
    K20_VACUUM_SERVICE_INFO,
    S10_VACUUM_SERVICE_INFO,
    S20_VACUUM_SERVICE_INFO,
)
from ._fixtures import mock_entry_factory

from tests.common import MockConfigEntry
from tests.components.bluetooth import inject_bluetooth_service_info
from tests.hass_fixtures import enable_bluetooth, hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test.cases(
    test.case("k20-start", sensor_type="k20_vacuum", service_info=K20_VACUUM_SERVICE_INFO, service=SERVICE_START, mock_method="clean_up"),
    test.case("k20-return", sensor_type="k20_vacuum", service_info=K20_VACUUM_SERVICE_INFO, service=SERVICE_RETURN_TO_BASE, mock_method="return_to_dock"),
    test.case("s10-start", sensor_type="s10_vacuum", service_info=S10_VACUUM_SERVICE_INFO, service=SERVICE_START, mock_method="clean_up"),
    test.case("s10-return", sensor_type="s10_vacuum", service_info=S10_VACUUM_SERVICE_INFO, service=SERVICE_RETURN_TO_BASE, mock_method="return_to_dock"),
    test.case("k10-combo-start", sensor_type="k10_pro_combo_vacumm", service_info=K10_POR_COMBO_VACUUM_SERVICE_INFO, service=SERVICE_START, mock_method="clean_up"),
    test.case("k10-combo-return", sensor_type="k10_pro_combo_vacumm", service_info=K10_POR_COMBO_VACUUM_SERVICE_INFO, service=SERVICE_RETURN_TO_BASE, mock_method="return_to_dock"),
    test.case("k10-start", sensor_type="k10_vacuum", service_info=K10_VACUUM_SERVICE_INFO, service=SERVICE_START, mock_method="clean_up"),
    test.case("k10-return", sensor_type="k10_vacuum", service_info=K10_VACUUM_SERVICE_INFO, service=SERVICE_RETURN_TO_BASE, mock_method="return_to_dock"),
    test.case("k10-pro-start", sensor_type="k10_pro_vacuum", service_info=K10_PRO_VACUUM_SERVICE_INFO, service=SERVICE_START, mock_method="clean_up"),
    test.case("k10-pro-return", sensor_type="k10_pro_vacuum", service_info=K10_PRO_VACUUM_SERVICE_INFO, service=SERVICE_RETURN_TO_BASE, mock_method="return_to_dock"),
    test.case("k11-start", sensor_type="k11+_vacuum", service_info=K11_PLUS_VACUUM_SERVICE_INFO, service=SERVICE_START, mock_method="clean_up"),
    test.case("k11-return", sensor_type="k11+_vacuum", service_info=K11_PLUS_VACUUM_SERVICE_INFO, service=SERVICE_RETURN_TO_BASE, mock_method="return_to_dock"),
    test.case("s20-start", sensor_type="s20_vacuum", service_info=S20_VACUUM_SERVICE_INFO, service=SERVICE_START, mock_method="clean_up"),
    test.case("s20-return", sensor_type="s20_vacuum", service_info=S20_VACUUM_SERVICE_INFO, service=SERVICE_RETURN_TO_BASE, mock_method="return_to_dock"),
)
async def vacuum_controlling(
    sensor_type: str,
    service_info: BluetoothServiceInfoBleak,
    service: str,
    mock_method: str,
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    entry_factory: Callable[[str], MockConfigEntry] = Depends(mock_entry_factory),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test switchbot vacuum controlling."""

    inject_bluetooth_service_info(hass, service_info)

    entry = entry_factory(sensor_type)
    entry.add_to_hass(hass)

    mocked_instance = AsyncMock(return_value=True)

    with patch.multiple(
        "homeassistant.components.switchbot.vacuum.switchbot.SwitchbotVacuum",
        update=MagicMock(return_value=None),
        **{mock_method: mocked_instance},
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        entity_id = "vacuum.test_name"

        await hass.services.async_call(
            VACUUM_DOMAIN,
            service,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        mocked_instance.assert_awaited_once()
