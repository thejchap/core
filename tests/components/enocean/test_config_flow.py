"""Tests for EnOcean config flow."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.enocean.config_flow import EnOceanFlowHandler
from homeassistant.components.enocean.const import DOMAIN, MANUFACTURER
from homeassistant.config_entries import (
    SOURCE_IMPORT,
    SOURCE_USB,
    SOURCE_USER,
    ConfigEntryState,
)
from homeassistant.const import CONF_DEVICE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.usb import UsbServiceInfo

from tests.common import MockConfigEntry
from tests.components.enocean._fixtures import mock_zeroconf
from tests.hass_fixtures import hass, mock_network

GATEWAY_CLASS = "homeassistant.components.enocean.config_flow.Gateway"
GLOB_METHOD = "homeassistant.components.enocean.config_flow.glob.glob"
SETUP_ENTRY_METHOD = "homeassistant.components.enocean.async_setup_entry"


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def user_flow_cannot_create_multiple_instances(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that the user flow aborts if an instance is already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_DEVICE: "/already/configured/path"}
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def user_flow_with_detected_dongle(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test the user flow with a detected EnOcean dongle."""
    FAKE_DONGLE_PATH = "/fake/dongle"

    with patch(GLOB_METHOD, side_effect=[[FAKE_DONGLE_PATH], [], []]):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("detect")
    devices = result["data_schema"].schema.get(CONF_DEVICE).config.get("options")
    expect(FAKE_DONGLE_PATH in devices).to_be(True)
    expect(EnOceanFlowHandler.MANUAL_PATH_VALUE in devices).to_be(True)


@test
async def user_flow_with_no_detected_dongle(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test the user flow with no detected EnOcean dongle."""
    with patch(GLOB_METHOD, return_value=[]):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("manual")


@test
async def detection_flow_with_valid_path(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test the detection flow with a valid path selected."""
    USER_PROVIDED_PATH = "/user/provided/path"

    with patch(
        GATEWAY_CLASS,
        return_value=Mock(start=AsyncMock(), stop=Mock()),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "detect"},
            data={CONF_DEVICE: USER_PROVIDED_PATH},
        )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["data"][CONF_DEVICE]).to_equal(USER_PROVIDED_PATH)


@test
async def detection_flow_with_custom_path(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test the detection flow with custom path selected."""
    USER_PROVIDED_PATH = EnOceanFlowHandler.MANUAL_PATH_VALUE

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "detect"},
        data={CONF_DEVICE: USER_PROVIDED_PATH},
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("manual")


@test
async def detection_flow_with_invalid_path(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test the detection flow with an invalid path selected."""
    USER_PROVIDED_PATH = "/invalid/path"

    with patch(
        GATEWAY_CLASS,
        return_value=Mock(
            start=AsyncMock(side_effect=ConnectionError("invalid path")), stop=Mock()
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "detect"},
            data={CONF_DEVICE: USER_PROVIDED_PATH},
        )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("manual")
    expect(CONF_DEVICE in result["errors"]).to_be(True)


@test
async def manual_flow_with_valid_path(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test the manual flow with a valid path."""
    USER_PROVIDED_PATH = "/user/provided/path"

    with patch(
        GATEWAY_CLASS,
        return_value=Mock(start=AsyncMock(), stop=Mock()),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "manual"}, data={CONF_DEVICE: USER_PROVIDED_PATH}
        )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["data"][CONF_DEVICE]).to_equal(USER_PROVIDED_PATH)


@test
async def manual_flow_with_invalid_path(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test the manual flow with an invalid path."""
    USER_PROVIDED_PATH = "/user/provided/path"

    with patch(
        GATEWAY_CLASS,
        return_value=Mock(
            start=AsyncMock(side_effect=ConnectionError("invalid path")), stop=Mock()
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "manual"}, data={CONF_DEVICE: USER_PROVIDED_PATH}
        )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("manual")
    expect(CONF_DEVICE in result["errors"]).to_be(True)


@test
async def import_flow_with_valid_path(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test the import flow with a valid path."""
    DATA_TO_IMPORT = {CONF_DEVICE: "/valid/path/to/import"}

    with patch(
        GATEWAY_CLASS,
        return_value=Mock(start=AsyncMock(), stop=Mock()),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=DATA_TO_IMPORT,
        )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["data"][CONF_DEVICE]).to_equal(DATA_TO_IMPORT[CONF_DEVICE])


@test
async def import_flow_with_invalid_path(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test the import flow with an invalid path."""
    DATA_TO_IMPORT = {CONF_DEVICE: "/invalid/path/to/import"}

    with patch(
        GATEWAY_CLASS,
        return_value=Mock(
            start=AsyncMock(side_effect=ConnectionError("invalid path")), stop=Mock()
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=DATA_TO_IMPORT,
        )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("invalid_dongle_path")


@test
async def usb_discovery(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test usb discovery success path."""
    usb_discovery_info = UsbServiceInfo(
        device="/dev/enocean0",
        pid="6001",
        vid="0403",
        serial_number="1234",
        description="USB 300",
        manufacturer="EnOcean GmbH",
    )
    device = "/dev/enocean0"
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USB},
        data=usb_discovery_info,
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("usb_confirm")
    expect(result["errors"] is None).to_be(True)

    with (
        patch(
            GATEWAY_CLASS,
            return_value=Mock(start=AsyncMock(), stop=Mock()),
        ),
        patch(SETUP_ENTRY_METHOD, AsyncMock(return_value=True)),
        patch(
            "homeassistant.components.usb.get_serial_by_id",
            side_effect=lambda x: x,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(MANUFACTURER)
    expect(result["data"]).to_equal({"device": device})
    expect(result["context"]["unique_id"]).to_equal(
        "0403:6001_1234_EnOcean GmbH_USB 300"
    )
    expect(result["context"]["title_placeholders"]).to_equal(
        {"name": "USB 300 - /dev/enocean0, s/n: 1234 - EnOcean GmbH - 0403:6001"}
    )
    expect(result["result"].state is ConfigEntryState.LOADED).to_be(True)


@test
async def usb_discovery_already_configured_updates_path(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test usb discovery aborts when already configured and updates device path."""
    existing_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DEVICE: "/dev/enocean-old"},
        unique_id="0403:6001_1234_EnOcean GmbH_USB 300",
    )
    existing_entry.add_to_hass(hass)

    usb_discovery_info = UsbServiceInfo(
        device="/dev/enocean-new",
        pid="6001",
        vid="0403",
        serial_number="1234",
        description="USB 300",
        manufacturer="EnOcean GmbH",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USB},
        data=usb_discovery_info,
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("single_instance_allowed")
