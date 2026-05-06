"""Test the eurotronic_cometblue config flow."""

from copy import deepcopy
from unittest.mock import AsyncMock, patch

from bleak.exc import BleakDeviceNotFoundError
from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.eurotronic_cometblue.config_flow import (
    name_from_discovery,
)
from homeassistant.components.eurotronic_cometblue.const import DOMAIN
from homeassistant.const import CONF_ADDRESS, CONF_PIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import FIXTURE_DEVICE_NAME, FIXTURE_MAC, FIXTURE_USER_INPUT
from ._fixtures import (
    FAKE_SERVICE_INFO,
    mock_ble_device,
    mock_config_entry,
    mock_service_info,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import enable_bluetooth, hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bluetooth: None = Depends(enable_bluetooth),
    _ble: None = Depends(mock_ble_device),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def user_step_no_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle no devices found."""
    with patch(
        "homeassistant.components.eurotronic_cometblue.config_flow.async_discovered_service_info",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("no_devices_found")

        setup_entry.assert_not_called()


@test.skip("requires MockCometBlueBleakClient autouse fixture")
async def user_step_discovered_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _service_info: None = Depends(mock_service_info),
) -> None:
    """Test we properly handle device picking."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pick_device")

    raised = False
    try:
        await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ADDRESS: "wrong_address"}
        )
    except vol.Invalid:
        raised = True
    expect(raised).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ADDRESS: FIXTURE_MAC}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=FIXTURE_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].title).to_equal(f"{FIXTURE_DEVICE_NAME} {FIXTURE_MAC}")
    expect(result["result"].unique_id).to_equal(FIXTURE_MAC)
    expect(result["result"].data).to_equal(
        {
            CONF_ADDRESS: FIXTURE_MAC,
            CONF_PIN: FIXTURE_USER_INPUT[CONF_PIN],
        }
    )
    setup_entry.assert_called_once()


@test
async def user_step_with_existing_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we properly handle device picking if entry exists."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=FAKE_SERVICE_INFO,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(setup_entry.call_count).to_equal(0)


@test.skip("requires MockCometBlueBleakClient autouse fixture")
async def bluetooth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we can handle a bluetooth discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=FAKE_SERVICE_INFO,
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        FIXTURE_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].title).to_equal(f"{FIXTURE_DEVICE_NAME} {FIXTURE_MAC}")
    expect(result["result"].unique_id).to_equal(FIXTURE_MAC)
    expect(result["result"].data).to_equal(
        {
            CONF_ADDRESS: FIXTURE_MAC,
            CONF_PIN: FIXTURE_USER_INPUT[CONF_PIN],
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.skip("requires MockCometBlueBleakClient autouse fixture")
@test.cases(
    test.case(
        "invalid_pin",
        patch_target="get_battery_async",
        side_effect=TimeoutError(),
        expected_error={"base": "invalid_pin"},
    ),
    test.case(
        "timeout_connect",
        patch_target="connect_async",
        side_effect=TimeoutError(),
        expected_error={"base": "timeout_connect"},
    ),
    test.case(
        "cannot_connect",
        patch_target="connect_async",
        side_effect=BleakDeviceNotFoundError(FAKE_SERVICE_INFO.address),
        expected_error={"base": "cannot_connect"},
    ),
    test.case(
        "unknown",
        patch_target="connect_async",
        side_effect=OSError("Something totally unexpected"),
        expected_error={"base": "unknown"},
    ),
)
async def bluetooth_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    patch_target: str,
    side_effect: Exception,
    expected_error: dict,
) -> None:
    """Test we can handle a bluetooth discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=FAKE_SERVICE_INFO,
    )

    with patch(
        f"homeassistant.components.eurotronic_cometblue.config_flow.AsyncCometBlue.{patch_target}",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")
    expect(result["errors"]).to_equal(expected_error)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        FIXTURE_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].title).to_equal(f"{FIXTURE_DEVICE_NAME} {FIXTURE_MAC}")
    expect(result["result"].unique_id).to_equal(FIXTURE_MAC)
    expect(result["result"].data).to_equal(
        {
            CONF_ADDRESS: FIXTURE_MAC,
            CONF_PIN: FIXTURE_USER_INPUT[CONF_PIN],
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def bluetooth_flow_no_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we can handle a bluetooth discovery flow with no device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=FAKE_SERVICE_INFO,
    )

    with patch(
        "homeassistant.components.eurotronic_cometblue.config_flow.async_ble_device_from_address",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def name_from_discovery_test(
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test we can create a name from discovery info."""
    expect(name_from_discovery(None)).to_equal("Comet Blue")

    fake_info = deepcopy(FAKE_SERVICE_INFO)
    fake_info.name = str(fake_info.address)
    expect(name_from_discovery(fake_info)).to_equal(str(fake_info.address))

    fake_info = deepcopy(FAKE_SERVICE_INFO)
    expect(name_from_discovery(fake_info)).to_equal(
        f"{FIXTURE_DEVICE_NAME} {FIXTURE_MAC}"
    )
