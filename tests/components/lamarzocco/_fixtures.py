"""Tryke fixtures for the lamarzocco integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from bleak.backends.device import BLEDevice
from pylamarzocco.const import ModelName
from pylamarzocco.models import (
    Thing,
    ThingDashboardConfig,
    ThingSchedulingSettings,
    ThingSettings,
    ThingStatistics,
)
from pylamarzocco.util import InstallationKey
from tryke import Depends, fixture

from homeassistant.components.lamarzocco.const import CONF_INSTALLATION_KEY, DOMAIN
from homeassistant.const import CONF_ADDRESS, CONF_MAC, CONF_TOKEN

from . import MOCK_INSTALLATION_KEY, SERIAL_DICT, USER_INPUT

from tests.common import MockConfigEntry, load_json_object_fixture


@fixture
def device_fixture() -> ModelName:
    """Return the device fixture for a specific device."""
    return ModelName.GS3_AV


@fixture
def mock_generate_installation_key() -> Generator[MagicMock]:
    """Return a mocked generate_installation_key."""
    with (
        patch(
            "homeassistant.components.lamarzocco.generate_installation_key",
            return_value=InstallationKey.from_json(MOCK_INSTALLATION_KEY),
        ) as mock_generate,
        patch(
            "homeassistant.components.lamarzocco.config_flow.generate_installation_key",
            new=mock_generate,
        ),
    ):
        yield mock_generate


@fixture
def mock_cloud_client() -> Generator[MagicMock]:
    """Return a mocked LM cloud client."""
    with (
        patch(
            "homeassistant.components.lamarzocco.config_flow.LaMarzoccoCloudClient",
            autospec=True,
        ) as cloud_client,
        patch(
            "homeassistant.components.lamarzocco.LaMarzoccoCloudClient",
            new=cloud_client,
        ),
    ):
        client = cloud_client.return_value
        client.list_things.return_value = [
            Thing.from_dict(load_json_object_fixture("thing.json", DOMAIN))
        ]
        client.get_thing_settings.return_value = ThingSettings.from_dict(
            load_json_object_fixture("settings.json", DOMAIN)
        )
        yield client


@fixture
def mock_lamarzocco(
    device_fixture: ModelName = Depends(device_fixture),
) -> Generator[MagicMock]:
    """Return a mocked LM client."""
    if device_fixture == ModelName.LINEA_MINI:
        config = load_json_object_fixture("config_mini.json", DOMAIN)
    elif device_fixture == ModelName.LINEA_MICRA:
        config = load_json_object_fixture("config_micra.json", DOMAIN)
    else:
        config = load_json_object_fixture("config_gs3.json", DOMAIN)
    schedule = load_json_object_fixture("schedule.json", DOMAIN)
    settings = load_json_object_fixture("settings.json", DOMAIN)
    statistics = load_json_object_fixture("statistics.json", DOMAIN)

    with patch(
        "homeassistant.components.lamarzocco.LaMarzoccoMachine",
        autospec=True,
    ) as machine_mock_init:
        machine_mock = machine_mock_init.return_value
        machine_mock.serial_number = SERIAL_DICT[device_fixture]
        machine_mock.dashboard = ThingDashboardConfig.from_dict(config)
        machine_mock.schedule = ThingSchedulingSettings.from_dict(schedule)
        machine_mock.settings = ThingSettings.from_dict(settings)
        machine_mock.statistics = ThingStatistics.from_dict(statistics)
        machine_mock.dashboard.model_name = device_fixture
        machine_mock.to_dict.return_value = {
            "serial_number": machine_mock.serial_number,
            "dashboard": machine_mock.dashboard.to_dict(),
            "schedule": machine_mock.schedule.to_dict(),
            "settings": machine_mock.settings.to_dict(),
        }
        machine_mock.connect_dashboard_websocket = AsyncMock()
        machine_mock.websocket = MagicMock()
        machine_mock.websocket.connected = True
        machine_mock.websocket.disconnect = AsyncMock()
        yield machine_mock


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.lamarzocco.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_config_entry(
    mock_lamarzocco: MagicMock = Depends(mock_lamarzocco),
) -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="My LaMarzocco",
        domain=DOMAIN,
        version=4,
        data=USER_INPUT
        | {
            CONF_ADDRESS: "000000000000",
            CONF_TOKEN: "token",
            CONF_INSTALLATION_KEY: MOCK_INSTALLATION_KEY,
        },
        unique_id=mock_lamarzocco.serial_number,
    )


@fixture
def mock_ble_device() -> BLEDevice:
    """Return a mock BLE device."""
    return BLEDevice("00:00:00:00:00:00", "GS_GS012345", details={"path": "path"})


@fixture
def mock_bluetooth_client() -> Generator[MagicMock]:
    """Return a mocked Bluetooth client."""
    with patch(
        "homeassistant.components.lamarzocco.LaMarzoccoBluetoothClient",
        autospec=True,
    ) as mock_bt_client_cls:
        mock_bt_client = mock_bt_client_cls.return_value
        mock_bt_client.disconnect = AsyncMock()
        yield mock_bt_client


@fixture
def mock_ble_device_from_address(
    mock_ble_device: BLEDevice = Depends(mock_ble_device),
) -> Generator[MagicMock]:
    """Return a mocked async_ble_device_from_address."""
    with patch(
        "homeassistant.components.lamarzocco.async_ble_device_from_address",
        return_value=mock_ble_device,
    ) as mock_addr:
        yield mock_addr


@fixture
def mock_config_entry_bluetooth(
    mock_lamarzocco: MagicMock = Depends(mock_lamarzocco),
    mock_ble_device: BLEDevice = Depends(mock_ble_device),
) -> MockConfigEntry:
    """Return a mocked config entry with Bluetooth enabled."""
    return MockConfigEntry(
        title=mock_lamarzocco.serial_number,
        domain=DOMAIN,
        version=4,
        data=USER_INPUT
        | {
            CONF_MAC: mock_ble_device.address,
            CONF_TOKEN: "token",
            CONF_INSTALLATION_KEY: MOCK_INSTALLATION_KEY,
        },
        unique_id=mock_lamarzocco.serial_number,
    )
