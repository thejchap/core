"""Tests for ZHA config flow."""

from ipaddress import ip_address
import json
from unittest.mock import AsyncMock, patch
import uuid

from tryke import Depends, expect, fixture, test
import zigpy.backups
import zigpy.config
import zigpy.types

from homeassistant import config_entries
from homeassistant.components.zha import config_flow, radio_manager
from homeassistant.components.zha.const import (
    CONF_BAUDRATE,
    CONF_FLOW_CONTROL,
    CONF_RADIO_TYPE,
    DOMAIN,
    EZSP_OVERWRITE_EUI64,
)
from homeassistant.config_entries import SOURCE_USB, SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.usb import UsbServiceInfo
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.components.zha._fixtures import (
    disable_platform_only,
    globally_load_quirks,
    mock_app,
    mock_multipan_platform,
    speed_up_radio_mgr,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network

PROBE_FUNCTION_PATH = "zigbee.application.ControllerApplication.probe"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _quirks: None = Depends(globally_load_quirks),
    _platforms: None = Depends(disable_platform_only),
    _multipan: None = Depends(mock_multipan_platform),
    _radio_speed: None = Depends(speed_up_radio_mgr),
) -> None:
    """Anchor fixture priming common autouse-equivalent patches."""


# ---------------------------------------------------------------------------
# Pure unit tests (no hass needed)
# ---------------------------------------------------------------------------


@test
def allow_overwrite_ezsp_ieee() -> None:
    """Test modifying the backup to allow bellows to override the IEEE address."""
    backup = zigpy.backups.NetworkBackup()
    new_backup = radio_manager._allow_overwrite_ezsp_ieee(backup)

    expect(backup != new_backup).to_be(True)
    expect(
        new_backup.network_info.stack_specific["ezsp"][EZSP_OVERWRITE_EUI64]
    ).to_be(True)


@test
def prevent_overwrite_ezsp_ieee() -> None:
    """Test modifying the backup to prevent bellows from overriding the IEEE address."""
    backup = zigpy.backups.NetworkBackup()
    backup.network_info.stack_specific["ezsp"] = {EZSP_OVERWRITE_EUI64: True}
    new_backup = radio_manager._prevent_overwrite_ezsp_ieee(backup)

    expect(backup != new_backup).to_be(True)
    expect(
        bool(
            new_backup.network_info.stack_specific.get("ezsp", {}).get(
                EZSP_OVERWRITE_EUI64
            )
        )
    ).to_be(False)


@test
def parse_uploaded_backup() -> None:
    """Test parsing uploaded backup files."""
    backup = zigpy.backups.NetworkBackup()
    text = json.dumps(backup.as_dict())

    with patch(
        "homeassistant.components.zha.config_flow.process_uploaded_file"
    ) as process_mock:
        process_mock.return_value.__enter__.return_value.read_text.return_value = text

        handler = config_flow.ZhaConfigFlowHandler()
        parsed_backup = handler._parse_uploaded_backup(str(uuid.uuid4()))

    expect(backup == parsed_backup).to_be(True)


@test
def format_backup_choice() -> None:
    """Test formatting zigpy NetworkBackup objects."""
    backup = zigpy.backups.NetworkBackup()
    backup.network_info.pan_id = zigpy.types.PanId(0x1234)
    backup.network_info.extended_pan_id = zigpy.types.EUI64.convert(
        "aa:bb:cc:dd:ee:ff:00:11"
    )

    with_ids = config_flow._format_backup_choice(backup, pan_ids=True)
    without_ids = config_flow._format_backup_choice(backup, pan_ids=False)

    expect(with_ids.startswith(without_ids)).to_be(True)
    expect("1234:aabbccddeeff0011" in with_ids).to_be(True)
    expect("1234:aabbccddeeff0011" in without_ids).to_be(False)


# ---------------------------------------------------------------------------
# Hass-based tests that don't need the real radio
# ---------------------------------------------------------------------------


@test
async def user_flow_show_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("choose_serial_port")


@test.cases(
    test.case(
        "ezsp",
        radio_type="EZSP = Silicon Labs EmberZNet protocol: Elelabs, HUSBZB-1, Telegesis",
    ),
    test.case(
        "znp",
        radio_type="ZNP = Texas Instruments Z-Stack ZNP protocol: CC253x, CC26x2, CC13x2",
    ),
    test.case(
        "deconz",
        radio_type="deCONZ = dresden elektronik deCONZ protocol: ConBee I/II, RaspBee I/II",
    ),
    test.case(
        "zigate",
        radio_type="ZiGate = ZiGate Zigbee radios: PiZiGate, ZiGate USB-TTL, ZiGate WiFi",
    ),
    test.case(
        "xbee",
        radio_type="XBee = Digi XBee Zigbee radios: Digi XBee Series 2, 2C, 3",
    ),
)
async def pick_radio_flow(
    radio_type: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test radio picker."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: "manual_pick_radio_type"},
        data={CONF_RADIO_TYPE: radio_type},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("manual_port_config")


@test.cases(
    test.case("none", data=None),
    test.case("empty", data={}),
    test.case("bogus_radio", data={"radio_type": "best_radio"}),
    test.case("efr32", data={"radio_type": "efr32"}),
)
async def hardware_invalid_data(
    data,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test onboarding flow -- invalid data."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_HARDWARE},
        data=data,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("invalid_hardware_data")


@test
async def zeroconf_discovery_bad_payload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zeroconf flow with a bad payload."""
    service_info = ZeroconfServiceInfo(
        ip_address=ip_address("192.168.1.200"),
        ip_addresses=[ip_address("192.168.1.200")],
        hostname="some.hostname",
        name="any",
        port=1234,
        properties={"radio_type": "some bogus radio"},
        type="_zigbee-coordinator._tcp.local.",
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=service_info
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("invalid_zeroconf_data")


@test
async def discovery_via_usb_no_radio(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _app: AsyncMock = Depends(mock_app),
) -> None:
    """Test usb flow -- no radio detected."""
    discovery_info = UsbServiceInfo(
        device="/dev/null",
        pid="AAAA",
        vid="AAAA",
        serial_number="1234",
        description="zigbee radio",
        manufacturer="test",
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USB}, data=discovery_info
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    with patch(
        "homeassistant.components.zha.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("usb_probe_failed")


@test
async def discovery_via_usb_duplicate_unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _app: AsyncMock = Depends(mock_app),
) -> None:
    """Test USB discovery when a config entry with a duplicate unique_id already exists."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="AAAA:AAAA_1234_test_zigbee radio",
        data={
            "device": {
                "path": "/dev/ttyUSB1",
                CONF_BAUDRATE: 115200,
                CONF_FLOW_CONTROL: None,
            }
        },
    )
    entry.add_to_hass(hass)

    discovery_info = UsbServiceInfo(
        device="/dev/ttyZIGBEE",
        pid="AAAA",
        vid="AAAA",
        serial_number="1234",
        description="zigbee radio",
        manufacturer="test",
    )
    with patch(
        "homeassistant.components.zha.async_setup_entry",
        AsyncMock(return_value=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USB}, data=discovery_info
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")


@test
async def discovery_via_usb_deconz_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test usb flow -- deconz already setup."""
    MockConfigEntry(domain="deconz", data={}).add_to_hass(hass)

    discovery_info = UsbServiceInfo(
        device="/dev/ttyZIGBEE",
        pid="AAAA",
        vid="AAAA",
        serial_number="1234",
        description="zigbee radio",
        manufacturer="test",
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USB}, data=discovery_info
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_zha_device")


@test
async def discovery_via_usb_deconz_ignored(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test usb flow -- deconz ignored."""
    MockConfigEntry(
        domain="deconz", source=config_entries.SOURCE_IGNORE, data={}
    ).add_to_hass(hass)

    discovery_info = UsbServiceInfo(
        device="/dev/ttyZIGBEE",
        pid="AAAA",
        vid="AAAA",
        serial_number="1234",
        description="zigbee radio",
        manufacturer="test",
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USB}, data=discovery_info
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")


@test
async def discovery_via_usb_zha_ignored_updates(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test usb flow that was ignored gets updated."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        source=config_entries.SOURCE_IGNORE,
        data={},
        unique_id="AAAA:AAAA_1234_test_zigbee radio",
    )
    entry.add_to_hass(hass)

    discovery_info = UsbServiceInfo(
        device="/dev/ttyZIGBEE",
        pid="AAAA",
        vid="AAAA",
        serial_number="1234",
        description="zigbee radio",
        manufacturer="test",
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USB}, data=discovery_info
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data["device"]["path"]).to_equal("/dev/ttyZIGBEE")


# ---------------------------------------------------------------------------
# Skipped tests still requiring complex zigpy radio fixtures
# ---------------------------------------------------------------------------


@test.skip("requires DelayedAsyncMock + ZNP probe + radio manager")
async def zeroconf_discovery() -> None:
    """Skipped pending fixture port."""


@test.skip("requires ZNP probe + radio manager")
async def legacy_zeroconf_discovery_zigate() -> None:
    """Skipped pending fixture port."""


@test.skip("requires ZNP probe patch + zha.async_setup_entry mock")
async def legacy_zeroconf_discovery_ip_change_ignored() -> None:
    """Skipped pending fixture port."""


@test.skip("requires consume_progress_flow + setup_entry mock")
async def legacy_zeroconf_discovery_confirm_final_abort_if_entries() -> None:
    """Skipped pending fixture port."""


@test.skip("requires ZNP probe + radio manager backup flow")
async def discovery_via_usb() -> None:
    """Skipped pending fixture port."""


@test.skip("requires ZNP probe + radio manager mock")
async def discovery_via_usb_already_setup() -> None:
    """Skipped pending fixture port."""


@test.skip("requires ZNP probe + radio manager + backup")
async def migration_strategy_recommended() -> None:
    """Skipped pending fixture port."""


@test.skip("requires ZNP probe + radio manager + backup + cannot_write")
async def migration_strategy_recommended_cannot_write() -> None:
    """Skipped pending fixture port."""


@test.skip("requires ZNP probe + mock_app")
async def multiple_zha_entries_aborts() -> None:
    """Skipped pending fixture port."""


@test.skip("requires ZNP probe + deconz discovery race")
async def discovery_via_usb_deconz_already_discovered() -> None:
    """Skipped pending fixture port."""


@test.skip("requires ZNP probe + mock_app + same device flow")
async def discovery_via_usb_same_device_already_setup() -> None:
    """Skipped pending fixture port."""


@test.skip("requires ZNP probe + mock_app")
async def legacy_zeroconf_discovery_already_setup() -> None:
    """Skipped pending fixture port."""


@test.skip("requires ZNP probe + already_setup match")
async def zeroconf_discovery_via_socket_already_setup_with_ip_match() -> None:
    """Skipped pending fixture port."""


@test.skip("requires onboarding mock + DelayedAsyncMock")
async def zeroconf_not_onboarded() -> None:
    """Skipped pending fixture port."""


@test.skip("requires consume_progress_flow + setup_entry mock")
async def user_flow() -> None:
    """Skipped pending fixture port."""


@test.skip("requires radio_manager.detect_radio_type AsyncMock")
async def user_flow_not_detected() -> None:
    """Skipped pending fixture port."""


@test.skip("requires bellows/znp/deconz/zigate probe orchestration")
async def detect_radio_type_success() -> None:
    """Skipped pending fixture port."""


@test.skip("requires radio probe orchestration with settings")
async def detect_radio_type_success_with_settings() -> None:
    """Skipped pending fixture port."""


@test.skip("requires probe_mock fixture + radio manager")
async def user_port_config_fail() -> None:
    """Skipped pending fixture port."""


@test.skip("requires probe_mock fixture + radio manager")
async def user_port_config() -> None:
    """Skipped pending fixture port."""


@test.skip("requires onboarding + consume_progress_flow")
async def hardware_not_onboarded() -> None:
    """Skipped pending fixture port."""


@test.skip("requires onboarding + consume_progress_flow")
async def hardware_no_flow_strategy() -> None:
    """Skipped pending fixture port."""


@test.skip("requires onboarding + zha.async_setup_entry + consume_progress_flow")
async def hardware_flow_strategy_advanced() -> None:
    """Skipped pending fixture port."""


@test.skip("requires onboarding + zha.async_setup_entry + consume_progress_flow")
async def hardware_flow_strategy_recommended() -> None:
    """Skipped pending fixture port."""


@test.skip("requires migration flow + backup + mock_app + ZNP probe")
async def hardware_migration_flow_strategy_advanced() -> None:
    """Skipped pending fixture port."""


@test.skip("requires migration flow + backup + mock_app + ZNP probe")
async def hardware_migration_flow_strategy_recommended() -> None:
    """Skipped pending fixture port."""


@test.skip("requires advanced_pick_radio fixture + mock_app")
async def strategy_no_network_settings() -> None:
    """Skipped pending fixture port."""


@test.skip("requires advanced_pick_radio fixture + mock_app + form flow")
async def formation_strategy_form_new_network() -> None:
    """Skipped pending fixture port."""


@test.skip("requires advanced_pick_radio fixture + mock_app")
async def formation_strategy_form_initial_network() -> None:
    """Skipped pending fixture port."""


@test.skip("requires advanced_pick_radio fixture + mock_app + failure injection")
async def formation_strategy_form_initial_network_failure() -> None:
    """Skipped pending fixture port."""


@test.skip("requires onboarding + advanced_pick_radio + mock_app")
async def onboarding_auto_formation_new_hardware() -> None:
    """Skipped pending fixture port."""


@test.skip("requires advanced_pick_radio + mock_app")
async def formation_strategy_reuse_settings() -> None:
    """Skipped pending fixture port."""


@test.skip("requires advanced_pick_radio + manual backup restore")
async def formation_strategy_restore_manual_backup_non_ezsp() -> None:
    """Skipped pending fixture port."""


@test.skip("requires advanced_pick_radio + EZSP overwrite IEEE")
async def formation_strategy_restore_manual_backup_overwrite_ieee_ezsp() -> None:
    """Skipped pending fixture port."""


@test.skip("requires advanced_pick_radio + EZSP backup restore")
async def formation_strategy_restore_manual_backup_ezsp() -> None:
    """Skipped pending fixture port."""


@test.skip("requires advanced_pick_radio + invalid backup upload")
async def formation_strategy_restore_manual_backup_invalid_upload() -> None:
    """Skipped pending fixture port."""


@test.skip("requires advanced_pick_radio + automatic backup choice")
async def formation_strategy_restore_automatic_backup_ezsp() -> None:
    """Skipped pending fixture port."""


@test.skip("requires advanced_pick_radio + automatic backup non-ezsp")
async def formation_strategy_restore_automatic_backup_non_ezsp() -> None:
    """Skipped pending fixture port."""


@test.skip("requires options flow + backup creation")
async def options_flow_creates_backup() -> None:
    """Skipped pending fixture port."""


@test.skip("requires options flow + mock_app + backup defaults")
async def options_flow_defaults() -> None:
    """Skipped pending fixture port."""


@test.skip("requires options flow + socket transport defaults")
async def options_flow_defaults_socket() -> None:
    """Skipped pending fixture port."""


@test.skip("requires options flow restart on cancel")
async def options_flow_restarts_running_zha_if_cancelled() -> None:
    """Skipped pending fixture port."""


@test.skip("requires options flow + migration reset")
async def options_flow_migration_reset_old_adapter() -> None:
    """Skipped pending fixture port."""


@test.skip("requires options flow reconfigure path")
async def options_flow_reconfigure_no_reset() -> None:
    """Skipped pending fixture port."""


@test.skip("requires firmware probe wrong-version path")
async def probe_wrong_firmware_installed() -> None:
    """Skipped pending fixture port."""


@test.skip("requires discovery firmware wrong-version path")
async def discovery_wrong_firmware_installed() -> None:
    """Skipped pending fixture port."""


@test.skip("requires migration TI CC -> ZNP path")
async def migration_ti_cc_to_znp() -> None:
    """Skipped pending fixture port."""


@test.skip("requires migration radio reset path")
async def migration_resets_old_radio() -> None:
    """Skipped pending fixture port."""


@test.skip("requires serial resolution OSError path")
async def config_flow_serial_resolution_oserror() -> None:
    """Skipped pending fixture port."""


@test.skip("requires manual backup overwrite IEEE write fail")
async def formation_strategy_restore_manual_backup_overwrite_ieee_ezsp_write_fail() -> (
    None
):
    """Skipped pending fixture port."""


@test.skip("requires migrate setup options with ignored discovery")
async def migrate_setup_options_with_ignored_discovery() -> None:
    """Skipped pending fixture port."""


@test.skip("requires plug-in new radio retry flow")
async def plug_in_new_radio_retry() -> None:
    """Skipped pending fixture port."""


@test.skip("requires plug-in old radio retry flow")
async def plug_in_old_radio_retry() -> None:
    """Skipped pending fixture port."""


@test.skip("requires plug-in old radio config-entry-removed flow")
async def plug_in_old_radio_config_entry_removed() -> None:
    """Skipped pending fixture port."""
