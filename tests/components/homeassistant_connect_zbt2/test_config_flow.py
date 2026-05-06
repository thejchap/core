"""Test the Home Assistant Connect ZBT-2 config flow."""

from unittest.mock import ANY, AsyncMock, Mock, call, patch

from tryke import Depends, expect, fixture, test
from universal_silabs_flasher.flasher import Zbt2Flasher

from homeassistant.components.homeassistant_connect_zbt2.const import DOMAIN
from homeassistant.components.homeassistant_hardware import (
    DOMAIN as HOMEASSISTANT_HARDWARE_DOMAIN,
)
from homeassistant.components.homeassistant_hardware.firmware_config_flow import (
    STEP_PICK_FIRMWARE_THREAD,
    STEP_PICK_FIRMWARE_ZIGBEE,
)
from homeassistant.components.homeassistant_hardware.helpers import (
    async_notify_firmware_info,
)
from homeassistant.components.homeassistant_hardware.util import (
    ApplicationType,
    FirmwareInfo,
)
from homeassistant.components.usb import DOMAIN as USB_DOMAIN, USBDevice
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.usb import UsbServiceInfo
from homeassistant.setup import async_setup_component

from ._fixtures import (
    addon_installed,
    autouse_bundle,
    start_addon,
    supervisor,
)
from .common import USB_DATA_ZBT2

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor(
    _autouse: None = Depends(autouse_bundle),
) -> None:
    """Local anchor fixture so tryke materializes hass per-test.

    Tryke needs the test signature to include a fixture Depends() that is
    defined in this same module for hass injection to land reliably; this
    re-exports the autouse bundle through a module-local name.
    """


@test
async def config_flow_zigbee(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test Zigbee config flow for Connect ZBT-2."""
    fw_type = ApplicationType.EZSP
    fw_version = "7.4.4.0 build 0"
    model = "Home Assistant Connect ZBT-2"
    usb_data = USB_DATA_ZBT2

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "usb"}, data=usb_data
    )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("pick_firmware")
    description_placeholders = result["description_placeholders"]
    expect(description_placeholders is not None).to_be(True)
    expect(description_placeholders["model"]).to_equal(model)

    async def mock_install_firmware_step(
        self,
        fw_update_url: str,
        fw_type: str,
        firmware_name: str,
        expected_installed_firmware_type: ApplicationType,
        step_id: str,
        next_step_id: str,
    ) -> ConfigFlowResult:
        self._probed_firmware_info = FirmwareInfo(
            device=usb_data.device,
            firmware_type=expected_installed_firmware_type,
            firmware_version=fw_version,
            owners=[],
            source="probe",
        )
        return await getattr(self, f"async_step_{next_step_id}")()

    with (
        patch(
            "homeassistant.components.homeassistant_hardware.firmware_config_flow.BaseFirmwareConfigFlow._install_firmware_step",
            autospec=True,
            side_effect=mock_install_firmware_step,
        ),
    ):
        pick_result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"next_step_id": STEP_PICK_FIRMWARE_ZIGBEE},
        )

        expect(pick_result["type"]).to_be(FlowResultType.MENU)
        expect(pick_result["step_id"]).to_equal("zigbee_installation_type")

        create_result = await hass.config_entries.flow.async_configure(
            pick_result["flow_id"],
            user_input={"next_step_id": "zigbee_intent_recommended"},
        )

    expect(create_result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    config_entry = create_result["result"]
    expect(config_entry.data).to_equal(
        {
            "firmware": fw_type.value,
            "firmware_version": fw_version,
            "device": usb_data.device,
            "manufacturer": usb_data.manufacturer,
            "pid": usb_data.pid,
            "product": usb_data.description,
            "serial_number": usb_data.serial_number,
            "vid": usb_data.vid,
        }
    )

    flows = hass.config_entries.flow.async_progress()

    # Ensure a ZHA discovery flow has been created
    expect(len(flows)).to_equal(1)
    zha_flow = flows[0]
    expect(zha_flow["handler"]).to_equal("zha")
    expect(zha_flow["context"]["source"]).to_equal("hardware")
    expect(zha_flow["step_id"]).to_equal("confirm")

    progress_zha_flows = hass.config_entries.flow._async_progress_by_handler(
        handler="zha",
        match_context=None,
    )

    expect(len(progress_zha_flows)).to_equal(1)

    # Ensure correct baudrate
    progress_zha_flow = progress_zha_flows[0]
    expect(progress_zha_flow.init_data).to_equal(
        {
            "flow_strategy": "recommended",
            "name": model,
            "port": {
                "path": usb_data.device,
                "baudrate": 460800,
                "flow_control": "hardware",
            },
            "radio_type": fw_type.value,
        }
    )


@test
async def config_flow_thread(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    _addon_installed: AsyncMock = Depends(addon_installed),
    _supervisor: None = Depends(supervisor),
    start_addon: AsyncMock = Depends(start_addon),
) -> None:
    """Test Thread config flow for Connect ZBT-2."""
    fw_type = ApplicationType.SPINEL
    fw_version = "2.4.4.0"
    model = "Home Assistant Connect ZBT-2"
    usb_data = USB_DATA_ZBT2

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "usb"}, data=usb_data
    )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("pick_firmware")
    description_placeholders = result["description_placeholders"]
    expect(description_placeholders is not None).to_be(True)
    expect(description_placeholders["model"]).to_equal(model)

    async def mock_install_firmware_step(
        self,
        fw_update_url: str,
        fw_type: str,
        firmware_name: str,
        expected_installed_firmware_type: ApplicationType,
        step_id: str,
        next_step_id: str,
    ) -> ConfigFlowResult:
        self._probed_firmware_info = FirmwareInfo(
            device=usb_data.device,
            firmware_type=expected_installed_firmware_type,
            firmware_version=fw_version,
            owners=[],
            source="probe",
        )
        return await getattr(self, f"async_step_{next_step_id}")()

    with (
        patch(
            "homeassistant.components.homeassistant_hardware.firmware_config_flow.BaseFirmwareConfigFlow._install_firmware_step",
            autospec=True,
            side_effect=mock_install_firmware_step,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"next_step_id": STEP_PICK_FIRMWARE_THREAD},
        )

        expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)
        expect(result["step_id"]).to_equal("start_otbr_addon")

        # Make sure the flow continues when the progress task is done.
        await hass.async_block_till_done()

        create_result = await hass.config_entries.flow.async_configure(
            result["flow_id"]
        )

    expect(start_addon.call_count).to_equal(1)
    expect(start_addon.call_args).to_equal(call("core_openthread_border_router"))
    expect(create_result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    config_entry = create_result["result"]
    expect(config_entry.data).to_equal(
        {
            "firmware": fw_type.value,
            "firmware_version": fw_version,
            "device": usb_data.device,
            "manufacturer": usb_data.manufacturer,
            "pid": usb_data.pid,
            "product": usb_data.description,
            "serial_number": usb_data.serial_number,
            "vid": usb_data.vid,
        }
    )

    flows = hass.config_entries.flow.async_progress()

    expect(len(flows)).to_equal(0)


@test.cases(
    test.case(
        "zbt2",
        usb_data=USB_DATA_ZBT2,
        model="Home Assistant Connect ZBT-2",
    ),
)
async def options_flow(
    usb_data: UsbServiceInfo,
    model: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test the options flow for Connect ZBT-2."""
    config_entry = MockConfigEntry(
        domain="homeassistant_connect_zbt2",
        data={
            "firmware": "spinel",
            "firmware_version": "SL-OPENTHREAD/2.4.4.0_GitHub-7074a43e4",
            "device": usb_data.device,
            "manufacturer": usb_data.manufacturer,
            "pid": usb_data.pid,
            "product": usb_data.description,
            "serial_number": usb_data.serial_number,
            "vid": usb_data.vid,
        },
        version=1,
        minor_version=1,
    )
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)

    # First step is confirmation
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("pick_firmware")
    description_placeholders = result["description_placeholders"]
    expect(description_placeholders is not None).to_be(True)
    expect(description_placeholders["firmware_type"]).to_equal("spinel")
    expect(description_placeholders["model"]).to_equal(model)

    mock_update_client = AsyncMock()
    mock_manifest = Mock()
    mock_firmware = Mock()
    mock_firmware.filename = "zbt2_zigbee_ncp_7.4.4.0.gbl"
    mock_firmware.metadata = {
        "ezsp_version": "7.4.4.0",
        "fw_type": "zbt2_zigbee_ncp",
        "metadata_version": 2,
    }
    mock_manifest.firmwares = [mock_firmware]
    mock_update_client.async_update_data.return_value = mock_manifest
    mock_update_client.async_fetch_firmware.return_value = b"firmware_data"

    with (
        patch(
            "homeassistant.components.homeassistant_hardware.firmware_config_flow.guess_hardware_owners",
            return_value=[],
        ),
        patch(
            "homeassistant.components.homeassistant_hardware.firmware_config_flow.FirmwareUpdateClient",
            return_value=mock_update_client,
        ),
        patch(
            "homeassistant.components.homeassistant_hardware.firmware_config_flow.async_flash_silabs_firmware",
            return_value=FirmwareInfo(
                device=usb_data.device,
                firmware_type=ApplicationType.EZSP,
                firmware_version="7.4.4.0 build 0",
                owners=[],
                source="probe",
            ),
        ) as flash_mock,
        patch(
            "homeassistant.components.homeassistant_hardware.firmware_config_flow.probe_silabs_firmware_info",
            side_effect=[
                # First call: probe before installation (returns current SPINEL firmware)
                FirmwareInfo(
                    device=usb_data.device,
                    firmware_type=ApplicationType.SPINEL,
                    firmware_version="2.4.4.0",
                    owners=[],
                    source="probe",
                ),
                # Second call: probe after installation (returns new EZSP firmware)
                FirmwareInfo(
                    device=usb_data.device,
                    firmware_type=ApplicationType.EZSP,
                    firmware_version="7.4.4.0 build 0",
                    owners=[],
                    source="probe",
                ),
            ],
        ),
        patch(
            "homeassistant.components.homeassistant_hardware.util.parse_firmware_image"
        ),
    ):
        pick_result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={"next_step_id": STEP_PICK_FIRMWARE_ZIGBEE},
        )

        expect(pick_result["type"]).to_be(FlowResultType.MENU)
        expect(pick_result["step_id"]).to_equal("zigbee_installation_type")

        create_result = await hass.config_entries.options.async_configure(
            pick_result["flow_id"],
            user_input={"next_step_id": "zigbee_intent_recommended"},
        )

    expect(create_result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    expect(config_entry.data).to_equal(
        {
            "firmware": "ezsp",
            "firmware_version": "7.4.4.0 build 0",
            "device": usb_data.device,
            "manufacturer": usb_data.manufacturer,
            "pid": usb_data.pid,
            "product": usb_data.description,
            "serial_number": usb_data.serial_number,
            "vid": usb_data.vid,
        }
    )

    expect(flash_mock.mock_calls).to_equal(
        [
            call(
                hass=hass,
                device=USB_DATA_ZBT2.device,
                fw_data=ANY,
                flasher_cls=Zbt2Flasher,
                expected_installed_firmware_type=ApplicationType.EZSP,
                progress_callback=ANY,
            )
        ]
    )

    flows = hass.config_entries.flow.async_progress()

    # Ensure a ZHA discovery flow has been created
    expect(len(flows)).to_equal(1)
    zha_flow = flows[0]
    expect(zha_flow["handler"]).to_equal("zha")
    expect(zha_flow["context"]["source"]).to_equal("hardware")
    expect(zha_flow["step_id"]).to_equal("confirm")

    progress_zha_flows = hass.config_entries.flow._async_progress_by_handler(
        handler="zha",
        match_context=None,
    )

    expect(len(progress_zha_flows)).to_equal(1)

    # Ensure correct baudrate
    progress_zha_flow = progress_zha_flows[0]
    expect(progress_zha_flow.init_data).to_equal(
        {
            "flow_strategy": "recommended",
            "name": model,
            "port": {
                "path": usb_data.device,
                "baudrate": 460800,
                "flow_control": "hardware",
            },
            "radio_type": "ezsp",
        }
    )


@test
async def duplicate_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test config flow unique_id deduplication."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "usb"}, data=USB_DATA_ZBT2
    )

    expect(result["type"]).to_be(FlowResultType.MENU)

    result_duplicate = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "usb"}, data=USB_DATA_ZBT2
    )

    expect(result_duplicate["type"]).to_be(FlowResultType.ABORT)
    expect(result_duplicate["reason"]).to_equal("already_in_progress")


@test
async def duplicate_discovery_updates_usb_path(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test config flow unique_id deduplication updates USB path."""
    config_entry = MockConfigEntry(
        domain="homeassistant_connect_zbt2",
        data={
            "firmware": "spinel",
            "firmware_version": "SL-OPENTHREAD/2.4.4.0_GitHub-7074a43e4",
            "device": "/dev/oldpath",
            "manufacturer": USB_DATA_ZBT2.manufacturer,
            "pid": USB_DATA_ZBT2.pid,
            "product": USB_DATA_ZBT2.description,
            "serial_number": USB_DATA_ZBT2.serial_number,
            "vid": USB_DATA_ZBT2.vid,
        },
        version=1,
        minor_version=1,
        unique_id=(
            f"{USB_DATA_ZBT2.vid}:{USB_DATA_ZBT2.pid}_"
            f"{USB_DATA_ZBT2.serial_number}_"
            f"{USB_DATA_ZBT2.manufacturer}_"
            f"{USB_DATA_ZBT2.description}"
        ),
    )
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "usb"}, data=USB_DATA_ZBT2
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(config_entry.data["device"]).to_equal(USB_DATA_ZBT2.device)


@test
async def firmware_callback_auto_creates_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test that firmware notification triggers import flow that auto-creates config entry."""
    await async_setup_component(hass, HOMEASSISTANT_HARDWARE_DOMAIN, {})
    await async_setup_component(hass, USB_DOMAIN, {})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "usb"}, data=USB_DATA_ZBT2
    )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("pick_firmware")

    usb_device = USBDevice(
        device=USB_DATA_ZBT2.device,
        vid=USB_DATA_ZBT2.vid,
        pid=USB_DATA_ZBT2.pid,
        serial_number=USB_DATA_ZBT2.serial_number,
        manufacturer=USB_DATA_ZBT2.manufacturer,
        description=USB_DATA_ZBT2.description,
    )

    with patch(
        "homeassistant.components.homeassistant_hardware.helpers.usb_device_from_path",
        return_value=usb_device,
    ):
        await async_notify_firmware_info(
            hass,
            "zha",
            FirmwareInfo(
                device=USB_DATA_ZBT2.device,
                firmware_type=ApplicationType.EZSP,
                firmware_version="7.4.4.0",
                owners=[],
                source="zha",
            ),
        )

        await hass.async_block_till_done()

    # The config entry was auto-created
    entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(entries)).to_equal(1)
    expect(entries[0].data).to_equal(
        {
            "device": USB_DATA_ZBT2.device,
            "firmware": ApplicationType.EZSP.value,
            "firmware_version": "7.4.4.0",
            "vid": USB_DATA_ZBT2.vid,
            "pid": USB_DATA_ZBT2.pid,
            "serial_number": USB_DATA_ZBT2.serial_number,
            "manufacturer": USB_DATA_ZBT2.manufacturer,
            "product": USB_DATA_ZBT2.description,
        }
    )

    # The discovery flow is gone
    expect(hass.config_entries.flow.async_progress_by_handler(DOMAIN)).to_equal([])


@test
async def firmware_callback_updates_existing_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test that firmware notification updates existing config entry device path."""
    await async_setup_component(hass, HOMEASSISTANT_HARDWARE_DOMAIN, {})
    await async_setup_component(hass, USB_DOMAIN, {})

    # Create existing config entry with old device path
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "firmware": ApplicationType.EZSP.value,
            "firmware_version": "7.4.4.0",
            "device": "/dev/oldpath",
            "vid": USB_DATA_ZBT2.vid,
            "pid": USB_DATA_ZBT2.pid,
            "serial_number": USB_DATA_ZBT2.serial_number,
            "manufacturer": USB_DATA_ZBT2.manufacturer,
            "product": USB_DATA_ZBT2.description,
        },
        unique_id=(
            f"{USB_DATA_ZBT2.vid}:{USB_DATA_ZBT2.pid}_"
            f"{USB_DATA_ZBT2.serial_number}_"
            f"{USB_DATA_ZBT2.manufacturer}_"
            f"{USB_DATA_ZBT2.description}"
        ),
    )
    config_entry.add_to_hass(hass)

    usb_device = USBDevice(
        device=USB_DATA_ZBT2.device,
        vid=USB_DATA_ZBT2.vid,
        pid=USB_DATA_ZBT2.pid,
        serial_number=USB_DATA_ZBT2.serial_number,
        manufacturer=USB_DATA_ZBT2.manufacturer,
        description=USB_DATA_ZBT2.description,
    )

    with patch(
        "homeassistant.components.homeassistant_hardware.helpers.usb_device_from_path",
        return_value=usb_device,
    ):
        await async_notify_firmware_info(
            hass,
            "zha",
            FirmwareInfo(
                device=USB_DATA_ZBT2.device,
                firmware_type=ApplicationType.EZSP,
                firmware_version="7.4.4.0",
                owners=[],
                source="zha",
            ),
        )

        await hass.async_block_till_done()

    # The config entry device path should be updated
    expect(config_entry.data["device"]).to_equal(USB_DATA_ZBT2.device)

    # No new config entry was created
    entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(entries)).to_equal(1)
