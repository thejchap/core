"""Test the Z-Wave JS config flow."""

from collections.abc import Generator
from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.usb import SerialDevice, USBDevice
from homeassistant.components.zwave_js.config_flow import TITLE, async_get_usb_ports
from homeassistant.components.zwave_js.const import ADDON_SLUG, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.esphome import ESPHomeServiceInfo
from homeassistant.helpers.service_info.hassio import HassioServiceInfo
from homeassistant.helpers.service_info.usb import UsbServiceInfo
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    mock_addon_setup_time,
    mock_get_server_version,
    mock_scan_serial_ports,
    mock_setup_entry,
    mock_supervisor,
    mock_usb_serial_by_id,
    set_country,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

ADDON_DISCOVERY_INFO = {
    "addon": "Z-Wave JS",
    "host": "host1",
    "port": 3001,
}

ESPHOME_DISCOVERY_INFO = ESPHomeServiceInfo(
    name="mock-name",
    zwave_home_id=1234,
    ip_address="192.168.1.100",
    port=6053,
)

USB_DISCOVERY_INFO = UsbServiceInfo(
    device="/dev/zwave",
    pid="AAAA",
    vid="AAAA",
    serial_number="1234",
    description="zwave radio",
    manufacturer="test",
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _scan: MagicMock = Depends(mock_scan_serial_ports),
    _by_id: MagicMock = Depends(mock_usb_serial_by_id),
    _addon_setup: None = Depends(mock_addon_setup_time),
    _country: None = Depends(set_country),
    _server_version: AsyncMock = Depends(mock_get_server_version),
) -> None:
    """Bundle the autouse-equivalent fixtures into one Depends target."""


@fixture
def mock_setup() -> Generator[AsyncMock]:
    """Patch ``async_setup`` to short-circuit integration setup hook."""
    with patch(
        "homeassistant.components.zwave_js.async_setup", return_value=True
    ) as setup:
        yield setup


# ---------------------------------------------------------------------------
# Manual / direct WebSocket URL flows.
# ---------------------------------------------------------------------------


@test
async def user_form_show(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the initial user form is shown for a new flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)


@test
async def manual(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup: AsyncMock = Depends(mock_setup),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we create an entry with the manual step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"], "initial form type").to_be(FlowResultType.FORM)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"url": "ws://localhost:3000"},
    )
    await hass.async_block_till_done()

    expect(result2["type"], "result type").to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"], "result title").to_equal("Z-Wave JS")
    expect(result2["data"], "result data").to_equal(
        {
            "url": "ws://localhost:3000",
            "usb_path": None,
            "socket_path": None,
            "s0_legacy_key": None,
            "s2_access_control_key": None,
            "s2_authenticated_key": None,
            "s2_unauthenticated_key": None,
            "lr_s2_access_control_key": None,
            "lr_s2_authenticated_key": None,
            "use_addon": False,
            "integration_created_addon": False,
        },
    )
    expect(len(mock_setup.mock_calls), "async_setup call count").to_be(1)
    expect(len(mock_setup_entry.mock_calls), "async_setup_entry call count").to_be(1)
    expect(result2["result"].unique_id, "unique id").to_equal("1234")


@test
async def manual_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that only one unique instance is allowed."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "url": "ws://localhost:3000",
            "use_addon": True,
            "integration_created_addon": True,
        },
        title=TITLE,
        unique_id="1234",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"], "form type").to_be(FlowResultType.FORM)
    expect(result["step_id"], "step id").to_equal("manual")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"url": "ws://1.1.1.1:3001"},
    )

    expect(result["type"], "result type").to_be(FlowResultType.ABORT)
    expect(result["reason"], "abort reason").to_equal("already_configured")
    expect(entry.data["url"], "entry url").to_equal("ws://1.1.1.1:3001")
    expect(entry.data["use_addon"], "use_addon updated").to_be(False)
    expect(entry.data["integration_created_addon"], "addon flag updated").to_be(False)


# ---------------------------------------------------------------------------
# Zeroconf discovery flow.
# ---------------------------------------------------------------------------


@test
async def zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup: AsyncMock = Depends(mock_setup),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the zeroconf discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="mock_hostname",
            name="mock_name",
            port=3000,
            type="_zwave-js-server._tcp.local.",
            properties={"homeId": "1234"},
        ),
    )

    expect(result["type"], "form type").to_be(FlowResultType.FORM)
    expect(result["step_id"], "step id").to_equal("zeroconf_confirm")

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows), "in-progress flow count").to_be(1)
    flow = flows[0]
    expect(flow["context"]["title_placeholders"]["host"], "host placeholder").to_equal(
        "127.0.0.1"
    )
    expect(flow["context"]["title_placeholders"]["port"], "port placeholder").to_equal(
        "3000"
    )
    expect(
        flow["context"]["title_placeholders"]["home_id"], "home_id placeholder"
    ).to_equal("0x000004d2")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()

    expect(result["type"], "result type").to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"], "result title").to_equal(TITLE)
    expect(result["data"], "result data").to_equal(
        {
            "url": "ws://127.0.0.1:3000",
            "usb_path": None,
            "socket_path": None,
            "s0_legacy_key": None,
            "s2_access_control_key": None,
            "s2_authenticated_key": None,
            "s2_unauthenticated_key": None,
            "lr_s2_access_control_key": None,
            "lr_s2_authenticated_key": None,
            "use_addon": False,
            "integration_created_addon": False,
        },
    )
    expect(len(mock_setup.mock_calls), "async_setup calls").to_be(1)
    expect(len(mock_setup_entry.mock_calls), "async_setup_entry calls").to_be(1)


# ---------------------------------------------------------------------------
# Discovery flow guards (no supervisor needed).
# ---------------------------------------------------------------------------


@test
async def usb_discovery_requires_supervisor(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test usb discovery flow is aborted when there is no supervisor."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USB},
        data=USB_DISCOVERY_INFO,
    )
    expect(result["type"], "result type").to_be(FlowResultType.ABORT)
    expect(result["reason"], "abort reason").to_equal("discovery_requires_supervisor")


@test
async def esphome_discovery_not_hassio(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test ESPHome discovery aborts when not hassio."""
    with patch(
        "homeassistant.components.zwave_js.config_flow.is_hassio", return_value=False
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ESPHOME},
            data=ESPHOME_DISCOVERY_INFO,
        )
    expect(result["type"], "result type").to_be(FlowResultType.ABORT)
    expect(result["reason"], "abort reason").to_equal("not_hassio")


# ---------------------------------------------------------------------------
# async_get_usb_ports helper tests (pure unit tests, no flow involved).
# ---------------------------------------------------------------------------


@test
async def get_usb_ports_filtering(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test get_usb_ports filters out 'n/a' descriptions when other ports exist."""
    mock_ports = [
        USBDevice(
            device="/dev/ttyUSB0",
            vid="1234",
            pid="5678",
            serial_number=None,
            manufacturer=None,
            description="n/a",
        ),
        USBDevice(
            device="/dev/ttyUSB1",
            vid="1234",
            pid="5678",
            serial_number=None,
            manufacturer=None,
            description="Device A",
        ),
        USBDevice(
            device="/dev/ttyUSB2",
            vid="1234",
            pid="5678",
            serial_number=None,
            manufacturer=None,
            description="N/A",
        ),
        USBDevice(
            device="/dev/ttyUSB3",
            vid="1234",
            pid="5678",
            serial_number=None,
            manufacturer=None,
            description="Device B",
        ),
    ]

    with patch(
        "homeassistant.components.zwave_js.config_flow.usb.async_scan_serial_ports",
        return_value=mock_ports,
    ):
        result = await async_get_usb_ports(hass)
        descriptions = list(result.values())

        expect(descriptions, "filtered descriptions").to_equal(
            [
                "Device A - /dev/ttyUSB1, s/n: n/a - 1234:5678",
                "Device B - /dev/ttyUSB3, s/n: n/a - 1234:5678",
            ]
        )


@test
async def get_usb_ports_all_na(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test get_usb_ports returns all ports when only 'n/a' descriptions exist."""
    mock_ports = [
        USBDevice(
            device="/dev/ttyUSB0",
            vid="1234",
            pid="5678",
            serial_number=None,
            manufacturer=None,
            description="n/a",
        ),
        USBDevice(
            device="/dev/ttyUSB1",
            vid="1234",
            pid="5678",
            serial_number=None,
            manufacturer=None,
            description="N/A",
        ),
        USBDevice(
            device="/dev/ttyUSB2",
            vid="1234",
            pid="5678",
            serial_number=None,
            manufacturer=None,
            description="n/a",
        ),
    ]

    with patch(
        "homeassistant.components.zwave_js.config_flow.usb.async_scan_serial_ports",
        return_value=mock_ports,
    ):
        result = await async_get_usb_ports(hass)
        descriptions = list(result.values())

        expect(len(descriptions), "all-na count").to_be(3)
        expect(
            all("n/a" in desc.lower() for desc in descriptions),
            "every description still 'n/a'",
        ).to_be(True)
        device_paths = [desc.split(" - ")[1].split(",")[0] for desc in descriptions]
        expect("/dev/ttyUSB0" in device_paths, "USB0 present").to_be(True)
        expect("/dev/ttyUSB1" in device_paths, "USB1 present").to_be(True)
        expect("/dev/ttyUSB2" in device_paths, "USB2 present").to_be(True)


@test
async def get_usb_ports_mixed_case_filtering(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test get_usb_ports filters 'n/a' case-insensitively."""
    mock_ports = [
        USBDevice(
            device="/dev/ttyUSB0",
            vid="1234",
            pid="5678",
            serial_number=None,
            manufacturer=None,
            description="n/a",
        ),
        USBDevice(
            device="/dev/ttyUSB1",
            vid="1234",
            pid="5678",
            serial_number=None,
            manufacturer=None,
            description="Device A",
        ),
        USBDevice(
            device="/dev/ttyUSB2",
            vid="1234",
            pid="5678",
            serial_number=None,
            manufacturer=None,
            description="N/A",
        ),
        USBDevice(
            device="/dev/ttyUSB3",
            vid="1234",
            pid="5678",
            serial_number=None,
            manufacturer=None,
            description="n/A",
        ),
        USBDevice(
            device="/dev/ttyUSB4",
            vid="1234",
            pid="5678",
            serial_number=None,
            manufacturer=None,
            description="Device B",
        ),
    ]

    with patch(
        "homeassistant.components.zwave_js.config_flow.usb.async_scan_serial_ports",
        return_value=mock_ports,
    ):
        result = await async_get_usb_ports(hass)
        descriptions = list(result.values())

        expect(descriptions, "filtered descriptions").to_equal(
            [
                "Device A - /dev/ttyUSB1, s/n: n/a - 1234:5678",
                "Device B - /dev/ttyUSB4, s/n: n/a - 1234:5678",
            ]
        )


@test
async def get_usb_ports_empty_list(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test get_usb_ports handles an empty port list."""
    with patch(
        "homeassistant.components.zwave_js.config_flow.usb.async_scan_serial_ports",
        return_value=[],
    ):
        result = await async_get_usb_ports(hass)
        expect(result, "empty result").to_equal({})


@test
async def get_usb_ports_single_na_port(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test get_usb_ports returns the single 'n/a' port if it's all that's available."""
    mock_ports = [
        USBDevice(
            device="/dev/ttyUSB0",
            vid="1234",
            pid="5678",
            serial_number=None,
            manufacturer=None,
            description="n/a",
        ),
    ]

    with patch(
        "homeassistant.components.zwave_js.config_flow.usb.async_scan_serial_ports",
        return_value=mock_ports,
    ):
        result = await async_get_usb_ports(hass)
        descriptions = list(result.values())
        expect(descriptions, "single n/a description").to_equal(
            ["n/a - /dev/ttyUSB0, s/n: n/a - 1234:5678"]
        )


@test
async def get_usb_ports_single_valid_port(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test get_usb_ports returns a single valid port (SerialDevice variant)."""
    mock_ports = [
        SerialDevice(
            device="/dev/ttyUSB0",
            serial_number=None,
            manufacturer=None,
            description="Device A",
        ),
    ]

    with patch(
        "homeassistant.components.zwave_js.config_flow.usb.async_scan_serial_ports",
        return_value=mock_ports,
    ):
        result = await async_get_usb_ports(hass)
        descriptions = list(result.values())
        expect(descriptions, "single valid description").to_equal(
            ["Device A - /dev/ttyUSB0, s/n: n/a"]
        )


@test
async def get_usb_ports_ignored_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test get_usb_ports filters out ignored non-Z-Wave devices."""
    mock_ports = [
        USBDevice(
            device="/dev/ttyUSB0",
            vid="10C4",
            pid="EA60",
            serial_number=None,
            manufacturer="Nabu Casa",
            description="ZBT-2",
        ),
        USBDevice(
            device="/dev/ttyUSB1",
            vid="10C4",
            pid="EA60",
            serial_number=None,
            manufacturer="Nabu Casa",
            description="SkyConnect v1.0",
        ),
        USBDevice(
            device="/dev/ttyUSB2",
            vid="10C4",
            pid="EA60",
            serial_number=None,
            manufacturer="Nabu Casa",
            description="Home Assistant Connect ZBT-1",
        ),
        USBDevice(
            device="/dev/ttyUSB3",
            vid="10C4",
            pid="EA60",
            serial_number=None,
            manufacturer="Nabu Casa",
            description="ZWA-2",
        ),
        USBDevice(
            device="/dev/ttyUSB4",
            vid="10C4",
            pid="EA60",
            serial_number=None,
            manufacturer="Another Manufacturer",
            description="Z-Wave USB Adapter",
        ),
        USBDevice(
            device="/dev/ttyUSB5",
            vid="10C4",
            pid="EA60",
            serial_number=None,
            manufacturer=None,
            description=None,
        ),
    ]

    with patch(
        "homeassistant.components.zwave_js.config_flow.usb.async_scan_serial_ports",
        return_value=mock_ports,
    ):
        result = await async_get_usb_ports(hass)
        descriptions = list(result.values())
        expect(descriptions, "filtered descriptions").to_equal(
            [
                "ZWA-2 - /dev/ttyUSB3, s/n: n/a - Nabu Casa - 10C4:EA60",
                "Z-Wave USB Adapter - /dev/ttyUSB4, s/n: n/a - Another Manufacturer - 10C4:EA60",
                "/dev/ttyUSB5, s/n: n/a - 10C4:EA60",
            ]
        )


# ---------------------------------------------------------------------------
# Skipped — depends on Supervisor / addon mocks not yet ported.
# ---------------------------------------------------------------------------


@test.skip("supervisor add-on fixtures not yet ported")
async def manual_errors() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_manual_errors() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def supervisor_discovery() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def supervisor_discovery_cannot_connect() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def clean_discovery_on_user_create() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def abort_discovery_with_existing_entry() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def abort_hassio_discovery_with_existing_flow() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def abort_hassio_discovery_for_other_addon() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def usb_discovery() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def usb_discovery_addon_not_running() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def usb_discovery_migration() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def usb_discovery_migration_restore_driver_ready_timeout() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def esphome_discovery_intent_custom() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def esphome_discovery_intent_recommended() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def esphome_discovery_already_configured() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def esphome_discovery_already_configured_unmanaged_addon() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def esphome_discovery_usb_same_home_id() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def discovery_addon_not_running() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def discovery_addon_not_installed() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def abort_usb_discovery_with_existing_flow() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def usb_discovery_with_existing_usb_flow() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def abort_usb_discovery_addon_required() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def usb_discovery_same_device() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def abort_usb_discovery_aborts_specific_devices() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def not_addon() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def addon_running() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def addon_running_failures() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def addon_running_already_configured() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def addon_installed() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def addon_installed_start_failure() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def addon_installed_failures() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def addon_installed_set_options_failure() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def addon_installed_usb_ports_failure() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def addon_installed_already_configured() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def addon_not_installed() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def install_addon_failure() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_manual() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_manual_different_device() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_not_addon() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_not_addon_with_addon() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_not_addon_with_addon_stop_fail() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_addon_running() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_addon_running_no_changes() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_different_device() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_addon_restart_failed() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_addon_running_server_info_failure() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_addon_not_installed() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_migrate_no_addon() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_migrate_low_sdk_version() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_migrate_with_addon() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_migrate_restore_driver_ready_timeout() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_migrate_backup_failure() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_migrate_backup_file_failure() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_migrate_start_addon_failure() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def reconfigure_migrate_restore_failure() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def get_driver_failure_intent_migrate() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def choose_serial_port_usb_ports_failure() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def configure_addon_usb_ports_failure() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def intent_recommended_user() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def recommended_usb_discovery() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def addon_rf_region_new_network() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def addon_rf_region_migrate_network() -> None:
    """Skipped pending Supervisor fixtures."""


@test.skip("supervisor add-on fixtures not yet ported")
async def addon_skip_rf_region() -> None:
    """Skipped pending Supervisor fixtures."""
