"""Test the Hue BLE config flow."""

from unittest.mock import AsyncMock, PropertyMock, patch

from HueBLE import ConnectionError, HueBleError, PairingError
from tryke import Depends, expect, fixture, test

from homeassistant.components.hue_ble.config_flow import Error
from homeassistant.components.hue_ble.const import (
    DOMAIN,
    URL_FACTORY_RESET,
    URL_PAIRING_MODE,
)
from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_USER
from homeassistant.const import CONF_MAC, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr

from . import (
    HUE_BLE_SERVICE_INFO,
    NOT_HUE_BLE_DISCOVERY_INFO,
    TEST_DEVICE_MAC,
    TEST_DEVICE_NAME,
)
from ._fixtures import mock_ble_device, mock_config_entry, mock_setup_entry

from tests.common import MockConfigEntry
from tests.components.bluetooth import generate_ble_device
from tests.hass_fixtures import hass as hass_fixture, mock_network

AUTH_ERROR = ConnectionError()
AUTH_ERROR.__cause__ = PairingError()


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _ble_device: AsyncMock = Depends(mock_ble_device),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user form."""
    with patch(
        "homeassistant.components.hue_ble.config_flow.bluetooth.async_discovered_service_info",
        return_value=[NOT_HUE_BLE_DISCOVERY_INFO, HUE_BLE_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["data_schema"].schema[CONF_MAC].container).to_equal(
        {
            HUE_BLE_SERVICE_INFO.address: (
                f"{HUE_BLE_SERVICE_INFO.name} ({HUE_BLE_SERVICE_INFO.address})"
            ),
        }
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_MAC: HUE_BLE_SERVICE_INFO.address},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")
    expect(result["description_placeholders"]).to_equal(
        {
            CONF_NAME: TEST_DEVICE_NAME,
            CONF_MAC: TEST_DEVICE_MAC,
            "url_pairing_mode": URL_PAIRING_MODE,
            "url_factory_reset": URL_FACTORY_RESET,
        }
    )

    with (
        patch(
            "homeassistant.components.hue_ble.config_flow.async_ble_device_from_address",
            return_value=generate_ble_device(TEST_DEVICE_NAME, TEST_DEVICE_MAC),
        ),
        patch(
            "homeassistant.components.hue_ble.config_flow.async_scanner_count",
            return_value=1,
        ),
        patch(
            "homeassistant.components.hue_ble.config_flow.HueBleLight.connect",
            side_effect=[True],
        ),
        patch(
            "homeassistant.components.hue_ble.config_flow.HueBleLight.poll_state",
            side_effect=[True],
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_DEVICE_NAME)
    expect(result["result"].unique_id).to_equal(dr.format_mac(TEST_DEVICE_MAC))
    expect(result["result"].data).to_equal({})

    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("not_hue_only", discovery_info=[NOT_HUE_BLE_DISCOVERY_INFO]),
    test.case("empty", discovery_info=[]),
)
async def user_form_no_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    discovery_info: list,
) -> None:
    """Test user form with no devices."""
    with patch(
        "homeassistant.components.hue_ble.config_flow.bluetooth.async_discovered_service_info",
        return_value=discovery_info,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test.cases(
    test.case(
        "no_scanners",
        mock_return_device=None,
        mock_scanner_count=0,
        mock_connect=None,
        mock_support_on_off=True,
        mock_poll_state=None,
        error=Error.NO_SCANNERS,
    ),
    test.case(
        "not_found",
        mock_return_device=None,
        mock_scanner_count=1,
        mock_connect=None,
        mock_support_on_off=True,
        mock_poll_state=None,
        error=Error.NOT_FOUND,
    ),
    test.case(
        "invalid_auth",
        mock_return_device=generate_ble_device(TEST_DEVICE_NAME, TEST_DEVICE_MAC),
        mock_scanner_count=1,
        mock_connect=AUTH_ERROR,
        mock_support_on_off=True,
        mock_poll_state=None,
        error=Error.INVALID_AUTH,
    ),
    test.case(
        "cannot_connect",
        mock_return_device=generate_ble_device(TEST_DEVICE_NAME, TEST_DEVICE_MAC),
        mock_scanner_count=1,
        mock_connect=ConnectionError,
        mock_support_on_off=True,
        mock_poll_state=None,
        error=Error.CANNOT_CONNECT,
    ),
    test.case(
        "not_supported",
        mock_return_device=generate_ble_device(TEST_DEVICE_NAME, TEST_DEVICE_MAC),
        mock_scanner_count=1,
        mock_connect=None,
        mock_support_on_off=False,
        mock_poll_state=None,
        error=Error.NOT_SUPPORTED,
    ),
    test.case(
        "cannot_poll",
        mock_return_device=generate_ble_device(TEST_DEVICE_NAME, TEST_DEVICE_MAC),
        mock_scanner_count=1,
        mock_connect=None,
        mock_support_on_off=True,
        mock_poll_state=HueBleError,
        error=Error.UNKNOWN,
    ),
    test.case(
        "unknown",
        mock_return_device=generate_ble_device(TEST_DEVICE_NAME, TEST_DEVICE_MAC),
        mock_scanner_count=1,
        mock_connect=HueBleError,
        mock_support_on_off=None,
        mock_poll_state=None,
        error=Error.UNKNOWN,
    ),
)
async def user_form_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    mock_return_device,
    mock_scanner_count: int,
    mock_connect,
    mock_support_on_off,
    mock_poll_state,
    error: Error,
) -> None:
    """Test user form with errors."""
    with patch(
        "homeassistant.components.hue_ble.config_flow.bluetooth.async_discovered_service_info",
        return_value=[NOT_HUE_BLE_DISCOVERY_INFO, HUE_BLE_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["data_schema"].schema[CONF_MAC].container).to_equal(
        {
            HUE_BLE_SERVICE_INFO.address: (
                f"{HUE_BLE_SERVICE_INFO.name} ({HUE_BLE_SERVICE_INFO.address})"
            ),
        }
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_MAC: HUE_BLE_SERVICE_INFO.address},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    with (
        patch(
            "homeassistant.components.hue_ble.config_flow.async_ble_device_from_address",
            return_value=mock_return_device,
        ),
        patch(
            "homeassistant.components.hue_ble.config_flow.async_scanner_count",
            return_value=mock_scanner_count,
        ),
        patch(
            "homeassistant.components.hue_ble.config_flow.HueBleLight.connect",
            side_effect=[mock_connect],
        ),
        patch(
            "homeassistant.components.hue_ble.config_flow.HueBleLight.supports_on_off",
            new_callable=PropertyMock,
            return_value=mock_support_on_off,
        ),
        patch(
            "homeassistant.components.hue_ble.config_flow.HueBleLight.poll_state",
            side_effect=[mock_poll_state],
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": error.value})

    with (
        patch(
            "homeassistant.components.hue_ble.config_flow.async_ble_device_from_address",
            return_value=generate_ble_device(TEST_DEVICE_NAME, TEST_DEVICE_MAC),
        ),
        patch(
            "homeassistant.components.hue_ble.config_flow.async_scanner_count",
            return_value=1,
        ),
        patch(
            "homeassistant.components.hue_ble.config_flow.HueBleLight.connect",
            side_effect=[True],
        ),
        patch(
            "homeassistant.components.hue_ble.config_flow.HueBleLight.poll_state",
            side_effect=[True],
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def bluetooth_discovery_aborts(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test bluetooth form aborts."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=HUE_BLE_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("discovery_unsupported")


@test
async def bluetooth_form_exception_already_set_up(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test bluetooth discovery form when device is already set up."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=HUE_BLE_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("discovery_unsupported")


@test
async def user_form_exception_already_set_up(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test user form when device is already set up."""
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.hue_ble.config_flow.bluetooth.async_discovered_service_info",
        return_value=[NOT_HUE_BLE_DISCOVERY_INFO, HUE_BLE_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["data_schema"].schema[CONF_MAC].container).to_equal(
        {
            HUE_BLE_SERVICE_INFO.address: (
                f"{HUE_BLE_SERVICE_INFO.name} ({HUE_BLE_SERVICE_INFO.address})"
            ),
        }
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_MAC: HUE_BLE_SERVICE_INFO.address},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
