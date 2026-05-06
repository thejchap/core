"""Test the Ubiquiti airOS config flow."""

from typing import Any
from unittest.mock import AsyncMock, patch

from airos.exceptions import (
    AirOSConnectionAuthenticationError,
    AirOSConnectionSetupError,
    AirOSDeviceConnectionError,
    AirOSEndpointError,
    AirOSKeyDataMissingError,
    AirOSListenerError,
)
from airos.helpers import DetectDeviceData
from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant.components.airos.const import (
    DEFAULT_USERNAME,
    DOMAIN,
    HOSTNAME,
    IP_ADDRESS,
    MAC_ADDRESS,
    SECTION_ADVANCED_SETTINGS,
)
from homeassistant.config_entries import (
    SOURCE_DHCP,
    SOURCE_REAUTH,
    SOURCE_RECONFIGURE,
    SOURCE_USER,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from . import AirOSData
from ._fixtures import (
    ap_status_fixture,
    mock_airos_client,
    mock_async_get_firmware_data,
    mock_config_entry,
    mock_discovery_method,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

NEW_PASSWORD = "new_password"
REAUTH_STEP = "reauth_confirm"
RECONFIGURE_STEP = "reconfigure"

MOCK_ADVANCED_SETTINGS = {
    CONF_SSL: True,
    CONF_VERIFY_SSL: False,
}

MOCK_CONFIG = {
    CONF_HOST: "1.1.1.1",
    CONF_USERNAME: DEFAULT_USERNAME,
    CONF_PASSWORD: "test-password",
    SECTION_ADVANCED_SETTINGS: MOCK_ADVANCED_SETTINGS,
}
MOCK_CONFIG_REAUTH = {
    CONF_HOST: "1.1.1.1",
    CONF_USERNAME: DEFAULT_USERNAME,
    CONF_PASSWORD: "wrong-password",
}

MOCK_DISC_DEV1 = {
    MAC_ADDRESS: "00:11:22:33:44:55",
    IP_ADDRESS: "192.168.1.100",
    HOSTNAME: "Test-Device-1",
}
MOCK_DISC_DEV2 = {
    MAC_ADDRESS: "AA:BB:CC:DD:EE:FF",
    IP_ADDRESS: "192.168.1.101",
    HOSTNAME: "Test-Device-2",
}
MOCK_DISC_EXISTS = {
    MAC_ADDRESS: "01:23:45:67:89:AB",
    IP_ADDRESS: "192.168.1.102",
    HOSTNAME: "Existing-Device",
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def manual_flow_creates_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ap_status: AirOSData = Depends(ap_status_fixture),
    _client: AsyncMock = Depends(mock_airos_client),
    _firmware: AsyncMock = Depends(mock_async_get_firmware_data),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the user form and create the appropriate entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect("manual" in result["menu_options"]).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "manual"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("manual")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_CONFIG
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("NanoStation 5AC ap name")
    expect(result["result"].unique_id).to_equal("01:23:45:67:89:AB")
    expect(result["data"]).to_equal(MOCK_CONFIG)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_airos_client),
    _firmware: AsyncMock = Depends(mock_async_get_firmware_data),
) -> None:
    """Test the form does not allow duplicate entries."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="01:23:45:67:89:AB",
        data=MOCK_CONFIG,
    )
    mock_entry.add_to_hass(hass)

    flow_start = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    menu = await hass.config_entries.flow.async_configure(
        flow_start["flow_id"], {"next_step_id": "manual"}
    )

    result = await hass.config_entries.flow.async_configure(
        menu["flow_id"], MOCK_CONFIG
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "invalid_auth",
        exception=AirOSConnectionAuthenticationError,
        error="invalid_auth",
    ),
    test.case(
        "cannot_connect_setup",
        exception=AirOSConnectionSetupError,
        error="cannot_connect",
    ),
    test.case(
        "cannot_connect_device",
        exception=AirOSDeviceConnectionError,
        error="cannot_connect",
    ),
    test.case(
        "key_data_missing",
        exception=AirOSKeyDataMissingError,
        error="key_data_missing",
    ),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def form_exception_handling(
    exception: type[Exception],
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    ap_status: AirOSData = Depends(ap_status_fixture),
    _client: AsyncMock = Depends(mock_airos_client),
    _firmware: AsyncMock = Depends(mock_async_get_firmware_data),
) -> None:
    """Test we handle exceptions."""
    with patch(
        "homeassistant.components.airos.config_flow.async_get_firmware_data",
        side_effect=exception,
    ):
        flow_start = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )

        menu = await hass.config_entries.flow.async_configure(
            flow_start["flow_id"], {"next_step_id": "manual"}
        )

        result = await hass.config_entries.flow.async_configure(
            menu["flow_id"], MOCK_CONFIG
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    fw_major = int(ap_status.host.fwversion.lstrip("v").split(".", 1)[0])
    valid_data = DetectDeviceData(
        fw_major=fw_major,
        mac=ap_status.derived.mac,
        hostname=ap_status.host.hostname,
    )

    with patch(
        "homeassistant.components.airos.config_flow.async_get_firmware_data",
        return_value=valid_data,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_CONFIG,
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("NanoStation 5AC ap name")
    expect(result["data"]).to_equal(MOCK_CONFIG)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def reauth_flow_scenario(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ap_status: AirOSData = Depends(ap_status_fixture),
    client: AsyncMock = Depends(mock_airos_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test successful reauthentication."""
    config_entry.add_to_hass(hass)

    client.login.side_effect = AirOSConnectionAuthenticationError
    await hass.config_entries.async_setup(config_entry.entry_id)

    with patch(
        "homeassistant.components.airos.config_flow.async_get_firmware_data",
        side_effect=AirOSConnectionAuthenticationError,
    ):
        flow = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_REAUTH, "entry_id": config_entry.entry_id},
            data=config_entry.data,
        )

    expect(flow["type"]).to_equal(FlowResultType.FORM)
    expect(flow["step_id"]).to_equal(REAUTH_STEP)

    fw_major = int(ap_status.host.fwversion.lstrip("v").split(".", 1)[0])
    valid_data = DetectDeviceData(
        fw_major=fw_major,
        mac=ap_status.derived.mac,
        hostname=ap_status.host.hostname,
    )

    mock_firmware = AsyncMock(return_value=valid_data)
    with (
        patch(
            "homeassistant.components.airos.config_flow.async_get_firmware_data",
            new=mock_firmware,
        ),
        patch(
            "homeassistant.components.airos.async_get_firmware_data",
            new=mock_firmware,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            user_input={CONF_PASSWORD: NEW_PASSWORD},
        )
        await hass.async_block_till_done(wait_background_tasks=True)

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    updated_entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    expect(updated_entry.data[CONF_PASSWORD]).to_equal(NEW_PASSWORD)


@test.cases(
    test.case(
        "invalid_auth",
        reauth_exception=AirOSConnectionAuthenticationError,
        expected_error="invalid_auth",
    ),
    test.case(
        "cannot_connect",
        reauth_exception=AirOSDeviceConnectionError,
        expected_error="cannot_connect",
    ),
    test.case(
        "key_data_missing",
        reauth_exception=AirOSKeyDataMissingError,
        expected_error="key_data_missing",
    ),
    test.case("unknown", reauth_exception=Exception, expected_error="unknown"),
)
async def reauth_flow_scenarios(
    reauth_exception: type[Exception],
    expected_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ap_status: AirOSData = Depends(ap_status_fixture),
    _client: AsyncMock = Depends(mock_airos_client),
    _firmware: AsyncMock = Depends(mock_async_get_firmware_data),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauthentication from start (failure) to finish (success)."""
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.airos.config_flow.async_get_firmware_data",
        side_effect=AirOSConnectionAuthenticationError,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)

        flow = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_REAUTH, "entry_id": config_entry.entry_id},
            data=config_entry.data,
        )

    expect(flow["type"]).to_equal(FlowResultType.FORM)
    expect(flow["step_id"]).to_equal(REAUTH_STEP)

    with patch(
        "homeassistant.components.airos.config_flow.async_get_firmware_data",
        side_effect=reauth_exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            user_input={CONF_PASSWORD: NEW_PASSWORD},
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal(REAUTH_STEP)
        expect(result["errors"]).to_equal({"base": expected_error})

    fw_major = int(ap_status.host.fwversion.lstrip("v").split(".", 1)[0])
    valid_data = DetectDeviceData(
        fw_major=fw_major,
        mac=ap_status.derived.mac,
        hostname=ap_status.host.hostname,
    )

    with patch(
        "homeassistant.components.airos.config_flow.async_get_firmware_data",
        new=AsyncMock(return_value=valid_data),
    ):
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            user_input={CONF_PASSWORD: NEW_PASSWORD},
        )

    expect(result["type"]).to_equal(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    updated_entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    expect(updated_entry.data[CONF_PASSWORD]).to_equal(NEW_PASSWORD)


@test
async def reauth_unique_id_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ap_status: AirOSData = Depends(ap_status_fixture),
    _client: AsyncMock = Depends(mock_airos_client),
    _firmware: AsyncMock = Depends(mock_async_get_firmware_data),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauthentication failure when the unique ID changes."""
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.airos.config_flow.async_get_firmware_data",
        side_effect=AirOSConnectionAuthenticationError,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)

        flow = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_REAUTH, "entry_id": config_entry.entry_id},
            data=config_entry.data,
        )

    fw_major = int(ap_status.host.fwversion.lstrip("v").split(".", 1)[0])
    valid_data = DetectDeviceData(
        fw_major=fw_major,
        mac="FF:23:45:67:89:AB",
        hostname=ap_status.host.hostname,
    )

    with patch(
        "homeassistant.components.airos.config_flow.async_get_firmware_data",
        new=AsyncMock(return_value=valid_data),
    ):
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            user_input={CONF_PASSWORD: NEW_PASSWORD},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")

    updated_entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    expect(updated_entry.data[CONF_PASSWORD] != NEW_PASSWORD).to_be(True)


@test
async def successful_reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_airos_client),
    _firmware: AsyncMock = Depends(mock_async_get_firmware_data),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test successful reconfigure."""
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": config_entry.entry_id},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(RECONFIGURE_STEP)

    user_input = {
        CONF_PASSWORD: NEW_PASSWORD,
        SECTION_ADVANCED_SETTINGS: {
            CONF_SSL: True,
            CONF_VERIFY_SSL: True,
        },
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=user_input,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    updated_entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    expect(updated_entry.data[CONF_PASSWORD]).to_equal(NEW_PASSWORD)
    expect(updated_entry.data[SECTION_ADVANCED_SETTINGS][CONF_SSL]).to_be(True)
    expect(updated_entry.data[SECTION_ADVANCED_SETTINGS][CONF_VERIFY_SSL]).to_be(True)

    expect(updated_entry.data[CONF_HOST]).to_equal(MOCK_CONFIG[CONF_HOST])
    expect(updated_entry.data[CONF_USERNAME]).to_equal(MOCK_CONFIG[CONF_USERNAME])


@test.cases(
    test.case(
        "invalid_auth",
        reconfigure_exception=AirOSConnectionAuthenticationError,
        expected_error="invalid_auth",
    ),
    test.case(
        "cannot_connect",
        reconfigure_exception=AirOSDeviceConnectionError,
        expected_error="cannot_connect",
    ),
    test.case(
        "key_data_missing",
        reconfigure_exception=AirOSKeyDataMissingError,
        expected_error="key_data_missing",
    ),
    test.case("unknown", reconfigure_exception=Exception, expected_error="unknown"),
)
async def reconfigure_flow_failure(
    reconfigure_exception: type[Exception],
    expected_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_airos_client),
    _firmware: AsyncMock = Depends(mock_async_get_firmware_data),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure from start (failure) to finish (success)."""
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": config_entry.entry_id},
    )

    user_input = {
        CONF_PASSWORD: NEW_PASSWORD,
        SECTION_ADVANCED_SETTINGS: {
            CONF_SSL: True,
            CONF_VERIFY_SSL: True,
        },
    }

    with patch(
        "homeassistant.components.airos.config_flow.async_get_firmware_data",
        side_effect=reconfigure_exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal(RECONFIGURE_STEP)
        expect(result["errors"]).to_equal({"base": expected_error})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=user_input,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    updated_entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    expect(updated_entry.data[CONF_PASSWORD]).to_equal(NEW_PASSWORD)


@test
async def reconfigure_unique_id_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ap_status: AirOSData = Depends(ap_status_fixture),
    _client: AsyncMock = Depends(mock_airos_client),
    _firmware: AsyncMock = Depends(mock_async_get_firmware_data),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguration failure when the unique ID changes."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": config_entry.entry_id},
    )
    flow_id = result["flow_id"]

    fw_major = int(ap_status.host.fwversion.lstrip("v").split(".", 1)[0])
    mismatched_data = DetectDeviceData(
        fw_major=fw_major,
        mac="FF:23:45:67:89:AB",
        hostname=ap_status.host.hostname,
    )

    user_input = {
        CONF_PASSWORD: NEW_PASSWORD,
        SECTION_ADVANCED_SETTINGS: {
            CONF_SSL: True,
            CONF_VERIFY_SSL: True,
        },
    }

    with patch(
        "homeassistant.components.airos.config_flow.async_get_firmware_data",
        new=AsyncMock(return_value=mismatched_data),
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            user_input=user_input,
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")

    updated_entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    expect(updated_entry.data[CONF_PASSWORD]).to_equal(MOCK_CONFIG[CONF_PASSWORD])
    expect(
        updated_entry.data[SECTION_ADVANCED_SETTINGS][CONF_SSL]
    ).to_equal(MOCK_CONFIG[SECTION_ADVANCED_SETTINGS][CONF_SSL])


@test
async def discover_flow_no_devices_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discovery: AsyncMock = Depends(mock_discovery_method),
) -> None:
    """Test discovery flow aborts when no devices are found."""
    discovery.return_value = {}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "discovery"}
    )

    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)
    expect(result["step_id"]).to_equal("discovery")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def discover_flow_one_device_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_airos_client),
    discovery: AsyncMock = Depends(mock_discovery_method),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test discovery flow goes straight to credentials when one device is found."""
    discovery.return_value = {MOCK_DISC_DEV1[MAC_ADDRESS]: MOCK_DISC_DEV1}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "discovery"}
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("configure_device")
    expect(result["description_placeholders"]["device_name"]).to_equal(
        MOCK_DISC_DEV1[HOSTNAME]
    )

    valid_data = DetectDeviceData(
        fw_major=8,
        mac=MOCK_DISC_DEV1[MAC_ADDRESS],
        hostname=MOCK_DISC_DEV1[HOSTNAME],
    )

    with patch(
        "homeassistant.components.airos.config_flow.async_get_firmware_data",
        new=AsyncMock(return_value=valid_data),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: DEFAULT_USERNAME,
                CONF_PASSWORD: "test-password",
                SECTION_ADVANCED_SETTINGS: MOCK_ADVANCED_SETTINGS,
            },
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MOCK_DISC_DEV1[HOSTNAME])
    expect(result["data"][CONF_HOST]).to_equal(MOCK_DISC_DEV1[IP_ADDRESS])


@test
async def discover_flow_multiple_devices_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_airos_client),
    _firmware: AsyncMock = Depends(mock_async_get_firmware_data),
    discovery: AsyncMock = Depends(mock_discovery_method),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test discovery flow with multiple devices found, requiring a selection step."""
    discovery.return_value = {
        MOCK_DISC_DEV1[MAC_ADDRESS]: MOCK_DISC_DEV1,
        MOCK_DISC_DEV2[MAC_ADDRESS]: MOCK_DISC_DEV2,
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect("discovery" in result["menu_options"]).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "discovery"}
    )

    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)
    expect(result["step_id"]).to_equal("discovery")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("select_device")

    expected_options = {
        MOCK_DISC_DEV1[MAC_ADDRESS]: (
            f"{MOCK_DISC_DEV1[HOSTNAME]} ({MOCK_DISC_DEV1[IP_ADDRESS]})"
        ),
        MOCK_DISC_DEV2[MAC_ADDRESS]: (
            f"{MOCK_DISC_DEV2[HOSTNAME]} ({MOCK_DISC_DEV2[IP_ADDRESS]})"
        ),
    }
    actual_options = result["data_schema"].schema[vol.Required(MAC_ADDRESS)].container
    expect(actual_options).to_equal(expected_options)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {MAC_ADDRESS: MOCK_DISC_DEV1[MAC_ADDRESS]}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("configure_device")
    expect(result["description_placeholders"]["device_name"]).to_equal(
        MOCK_DISC_DEV1[HOSTNAME]
    )

    valid_data = DetectDeviceData(
        fw_major=8,
        mac=MOCK_DISC_DEV1[MAC_ADDRESS],
        hostname=MOCK_DISC_DEV1[HOSTNAME],
    )

    with patch(
        "homeassistant.components.airos.config_flow.async_get_firmware_data",
        new=AsyncMock(return_value=valid_data),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: DEFAULT_USERNAME,
                CONF_PASSWORD: "test-password",
                SECTION_ADVANCED_SETTINGS: MOCK_ADVANCED_SETTINGS,
            },
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MOCK_DISC_DEV1[HOSTNAME])
    expect(result["data"][CONF_HOST]).to_equal(MOCK_DISC_DEV1[IP_ADDRESS])


@test
async def discover_flow_with_existing_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discovery: AsyncMock = Depends(mock_discovery_method),
    _client: AsyncMock = Depends(mock_airos_client),
) -> None:
    """Test that discovery ignores devices that are already configured."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCK_DISC_EXISTS[MAC_ADDRESS],
        data=MOCK_CONFIG,
    )
    mock_entry.add_to_hass(hass)

    discovery.return_value = {
        MOCK_DISC_DEV1[MAC_ADDRESS]: MOCK_DISC_DEV1,
        MOCK_DISC_EXISTS[MAC_ADDRESS]: MOCK_DISC_EXISTS,
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "discovery"}
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("configure_device")
    expect(result["description_placeholders"]["device_name"]).to_equal(
        MOCK_DISC_DEV1[HOSTNAME]
    )


@test.cases(
    test.case(
        "detect_error", exception=AirOSEndpointError, reason="detect_error"
    ),
    test.case(
        "listen_error", exception=AirOSListenerError, reason="listen_error"
    ),
    test.case("discovery_failed", exception=Exception, reason="discovery_failed"),
)
async def discover_flow_discovery_exceptions(
    exception: type[Exception],
    reason: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discovery: AsyncMock = Depends(mock_discovery_method),
) -> None:
    """Test discovery flow aborts on various discovery exceptions."""
    discovery.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "discovery"}
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(reason)


@test
async def configure_device_flow_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discovery: AsyncMock = Depends(mock_discovery_method),
    _client: AsyncMock = Depends(mock_airos_client),
) -> None:
    """Test configure_device step handles authentication and connection exceptions."""
    discovery.return_value = {MOCK_DISC_DEV1[MAC_ADDRESS]: MOCK_DISC_DEV1}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "discovery"}
    )

    with patch(
        "homeassistant.components.airos.config_flow.async_get_firmware_data",
        side_effect=AirOSConnectionAuthenticationError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "wrong-user",
                CONF_PASSWORD: "wrong-password",
                SECTION_ADVANCED_SETTINGS: MOCK_ADVANCED_SETTINGS,
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    with patch(
        "homeassistant.components.airos.config_flow.async_get_firmware_data",
        side_effect=AirOSDeviceConnectionError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: DEFAULT_USERNAME,
                CONF_PASSWORD: "some-password",
                SECTION_ADVANCED_SETTINGS: MOCK_ADVANCED_SETTINGS,
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def dhcp_ip_changed_updates_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """DHCP event with new IP should update the config entry and reload."""
    config_entry.add_to_hass(hass)

    macaddress = config_entry.unique_id.lower().replace(":", "").replace("-", "")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="1.1.1.2",
            hostname="airos",
            macaddress=macaddress,
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(config_entry.data[CONF_HOST]).to_equal("1.1.1.2")


@test
async def dhcp_mac_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """DHCP event with non-matching MAC should abort."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="1.1.1.2",
            hostname="airos",
            macaddress="aabbccddeeff",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unreachable")


@test
async def dhcp_ip_unchanged(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """DHCP event with same IP should abort."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip=config_entry.data[CONF_HOST],
            hostname="airos",
            macaddress=config_entry.unique_id.lower()
            .replace(":", "")
            .replace("-", ""),
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
