"""Test the switchbot locks."""

from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock, patch

from switchbot import SwitchbotOperationError
from tryke import Depends, expect, fixture, test

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.components.lock import DOMAIN as LOCK_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_LOCK,
    SERVICE_OPEN,
    SERVICE_UNLOCK,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from . import (
    LOCK_LITE_SERVICE_INFO,
    LOCK_SERVICE_INFO,
    LOCK_ULTRA_SERVICE_INFO,
    WOLOCKPRO_SERVICE_INFO,
)
from ._fixtures import mock_entry_encrypted_factory

from tests.common import MockConfigEntry
from tests.components.bluetooth import inject_bluetooth_service_info
from tests.hass_fixtures import enable_bluetooth, hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test.cases(
    test.case("lock_pro-unlock", sensor_type="lock_pro", service=SERVICE_UNLOCK, mock_method="unlock", service_info=WOLOCKPRO_SERVICE_INFO),
    test.case("lock_pro-lock", sensor_type="lock_pro", service=SERVICE_LOCK, mock_method="lock", service_info=WOLOCKPRO_SERVICE_INFO),
    test.case("lock-unlock", sensor_type="lock", service=SERVICE_UNLOCK, mock_method="unlock", service_info=LOCK_SERVICE_INFO),
    test.case("lock-lock", sensor_type="lock", service=SERVICE_LOCK, mock_method="lock", service_info=LOCK_SERVICE_INFO),
    test.case("lock_lite-unlock", sensor_type="lock_lite", service=SERVICE_UNLOCK, mock_method="unlock", service_info=LOCK_LITE_SERVICE_INFO),
    test.case("lock_lite-lock", sensor_type="lock_lite", service=SERVICE_LOCK, mock_method="lock", service_info=LOCK_LITE_SERVICE_INFO),
    test.case("lock_ultra-unlock", sensor_type="lock_ultra", service=SERVICE_UNLOCK, mock_method="unlock", service_info=LOCK_ULTRA_SERVICE_INFO),
    test.case("lock_ultra-lock", sensor_type="lock_ultra", service=SERVICE_LOCK, mock_method="lock", service_info=LOCK_ULTRA_SERVICE_INFO),
)
async def lock_services(
    sensor_type: str,
    service: str,
    mock_method: str,
    service_info: BluetoothServiceInfoBleak,
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    entry_factory: Callable[[str], MockConfigEntry] = Depends(
        mock_entry_encrypted_factory
    ),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test lock and unlock services on lock and lockpro devices."""
    inject_bluetooth_service_info(hass, service_info)

    entry = entry_factory(sensor_type=sensor_type)
    entry.add_to_hass(hass)
    mocked_instance = AsyncMock(return_value=True)

    with patch.multiple(
        "homeassistant.components.switchbot.lock.switchbot.SwitchbotLock",
        update=AsyncMock(return_value=None),
        **{mock_method: mocked_instance},
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        entity_id = "lock.test_name"

        await hass.services.async_call(
            LOCK_DOMAIN,
            service,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        mocked_instance.assert_awaited_once()


@test.cases(
    test.case("lock_pro-unlock", sensor_type="lock_pro", service=SERVICE_UNLOCK, mock_method="unlock_without_unlatch", service_info=WOLOCKPRO_SERVICE_INFO),
    test.case("lock_pro-open", sensor_type="lock_pro", service=SERVICE_OPEN, mock_method="unlock", service_info=WOLOCKPRO_SERVICE_INFO),
    test.case("lock-unlock", sensor_type="lock", service=SERVICE_UNLOCK, mock_method="unlock_without_unlatch", service_info=LOCK_SERVICE_INFO),
    test.case("lock-open", sensor_type="lock", service=SERVICE_OPEN, mock_method="unlock", service_info=LOCK_SERVICE_INFO),
    test.case("lock_lite-unlock", sensor_type="lock_lite", service=SERVICE_UNLOCK, mock_method="unlock_without_unlatch", service_info=LOCK_LITE_SERVICE_INFO),
    test.case("lock_lite-open", sensor_type="lock_lite", service=SERVICE_OPEN, mock_method="unlock", service_info=LOCK_LITE_SERVICE_INFO),
    test.case("lock_ultra-unlock", sensor_type="lock_ultra", service=SERVICE_UNLOCK, mock_method="unlock_without_unlatch", service_info=LOCK_ULTRA_SERVICE_INFO),
    test.case("lock_ultra-open", sensor_type="lock_ultra", service=SERVICE_OPEN, mock_method="unlock", service_info=LOCK_ULTRA_SERVICE_INFO),
)
async def lock_services_with_night_latch_enabled(
    sensor_type: str,
    service: str,
    mock_method: str,
    service_info: BluetoothServiceInfoBleak,
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    entry_factory: Callable[[str], MockConfigEntry] = Depends(
        mock_entry_encrypted_factory
    ),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test lock service when night latch enabled."""
    inject_bluetooth_service_info(hass, service_info)

    entry = entry_factory(sensor_type=sensor_type)
    entry.add_to_hass(hass)
    mocked_instance = AsyncMock(return_value=True)

    with patch.multiple(
        "homeassistant.components.switchbot.lock.switchbot.SwitchbotLock",
        is_night_latch_enabled=MagicMock(return_value=True),
        update=AsyncMock(return_value=None),
        **{mock_method: mocked_instance},
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        entity_id = "lock.test_name"

        await hass.services.async_call(
            LOCK_DOMAIN,
            service,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        mocked_instance.assert_awaited_once()


@test.cases(
    test.case("lock", service=SERVICE_LOCK, mock_method="lock"),
    test.case("open", service=SERVICE_OPEN, mock_method="unlock"),
    test.case("unlock", service=SERVICE_UNLOCK, mock_method="unlock_without_unlatch"),
)
async def exception_handling_lock_service(
    service: str,
    mock_method: str,
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    entry_factory: Callable[[str], MockConfigEntry] = Depends(
        mock_entry_encrypted_factory
    ),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test exception handling for lock service with exception."""
    inject_bluetooth_service_info(hass, LOCK_SERVICE_INFO)

    entry = entry_factory(sensor_type="lock")
    entry.add_to_hass(hass)
    entity_id = "lock.test_name"

    with patch.multiple(
        "homeassistant.components.switchbot.lock.switchbot.SwitchbotLock",
        is_night_latch_enabled=MagicMock(return_value=True),
        update=AsyncMock(return_value=None),
        **{mock_method: AsyncMock(side_effect=SwitchbotOperationError("Operation failed"))},
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        raised = False
        try:
            await hass.services.async_call(
                LOCK_DOMAIN,
                service,
                {ATTR_ENTITY_ID: entity_id},
                blocking=True,
            )
        except HomeAssistantError:
            raised = True
        expect(raised).to_be(True)
