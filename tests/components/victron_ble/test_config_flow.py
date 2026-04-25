"""Test the Victron Bluetooth Low Energy config flow."""

from unittest.mock import AsyncMock, patch

from home_assistant_bluetooth import BluetoothServiceInfo
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.victron_ble.const import DOMAIN
from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_USER
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_config_entry,
    mock_config_entry_added_to_hass,
    mock_discovered_service_info,
    mock_setup_entry,
)
from .fixtures import (
    NOT_VICTRON_SERVICE_INFO,
    VICTRON_INVERTER_SERVICE_INFO,
    VICTRON_TEST_WRONG_TOKEN,
    VICTRON_VEBUS_SERVICE_INFO,
    VICTRON_VEBUS_TOKEN,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    enable_bluetooth,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bluetooth: None = Depends(enable_bluetooth),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def async_step_bluetooth_valid_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test discovery via bluetooth with a valid device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=VICTRON_VEBUS_SERVICE_INFO,
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("access_token")

    # test valid access token
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCESS_TOKEN: VICTRON_VEBUS_TOKEN},
    )
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal(VICTRON_VEBUS_SERVICE_INFO.name)
    flow_result = result.get("result")
    expect(flow_result is not None).to_be(True)
    expect(flow_result.unique_id).to_equal(VICTRON_VEBUS_SERVICE_INFO.address)
    expect(flow_result.data).to_equal(
        {
            CONF_ACCESS_TOKEN: VICTRON_VEBUS_TOKEN,
        }
    )
    expect(set(flow_result.data.keys())).to_equal({CONF_ACCESS_TOKEN})


@test
async def async_step_bluetooth_invalid_key_retry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test wrong key via bluetooth discovery shows error and allows retry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=VICTRON_VEBUS_SERVICE_INFO,
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("access_token")

    # enter wrong key
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCESS_TOKEN: VICTRON_TEST_WRONG_TOKEN},
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("access_token")
    expect(result.get("errors")).to_equal({"base": "invalid_access_token"})

    # retry with correct key
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCESS_TOKEN: VICTRON_VEBUS_TOKEN},
    )
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal(VICTRON_VEBUS_SERVICE_INFO.name)


@test.cases(
    test.case(
        "bluetooth_not_victron",
        source=SOURCE_BLUETOOTH,
        service_info=NOT_VICTRON_SERVICE_INFO,
        expected_reason="not_supported",
    ),
    test.case(
        "bluetooth_unsupported_device",
        source=SOURCE_BLUETOOTH,
        service_info=VICTRON_INVERTER_SERVICE_INFO,
        expected_reason="not_supported",
    ),
    test.case(
        "user_no_devices",
        source=SOURCE_USER,
        service_info=None,
        expected_reason="no_devices_found",
    ),
)
async def abort_scenarios(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    source: str,
    service_info: BluetoothServiceInfo | None,
    expected_reason: str,
) -> None:
    """Test flows that result in abort."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": source},
        data=service_info,
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal(expected_reason)


@test
async def async_step_user_with_devices_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _discovered: AsyncMock = Depends(mock_discovered_service_info),
) -> None:
    """Test setup from service info cache with devices found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ADDRESS: VICTRON_VEBUS_SERVICE_INFO.address},
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("access_token")

    # test invalid access token shows error and allows retry
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ACCESS_TOKEN: VICTRON_TEST_WRONG_TOKEN}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("access_token")
    expect(result.get("errors")).to_equal({"base": "invalid_access_token"})

    # test retry with valid access token succeeds
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCESS_TOKEN: VICTRON_VEBUS_TOKEN},
    )
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal(VICTRON_VEBUS_SERVICE_INFO.name)


@test
async def async_step_user_device_added_between_steps(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _discovered: AsyncMock = Depends(mock_discovered_service_info),
) -> None:
    """Test abort when the device gets added via another flow between steps."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"address": VICTRON_VEBUS_SERVICE_INFO.address},
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test
async def async_step_user_with_found_devices_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_entry: MockConfigEntry = Depends(mock_config_entry_added_to_hass),
    _discovered: AsyncMock = Depends(mock_discovered_service_info),
) -> None:
    """Test setup from service info cache with devices found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("no_devices_found")


@test
async def async_step_bluetooth_devices_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_entry: MockConfigEntry = Depends(mock_config_entry_added_to_hass),
) -> None:
    """Test we can't start a flow if there is already a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=VICTRON_VEBUS_SERVICE_INFO,
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test
async def async_step_bluetooth_already_in_progress(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can't start a flow for the same device twice."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=VICTRON_VEBUS_SERVICE_INFO,
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("access_token")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=VICTRON_VEBUS_SERVICE_INFO,
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_in_progress")


@test
async def async_step_reauth_valid_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _discovered: AsyncMock = Depends(mock_discovered_service_info),
) -> None:
    """Test reauth flow with a valid new key."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ADDRESS: VICTRON_VEBUS_SERVICE_INFO.address,
            CONF_ACCESS_TOKEN: VICTRON_TEST_WRONG_TOKEN,
        },
        unique_id=VICTRON_VEBUS_SERVICE_INFO.address,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCESS_TOKEN: VICTRON_VEBUS_TOKEN},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data[CONF_ACCESS_TOKEN]).to_equal(VICTRON_VEBUS_TOKEN)


@test
async def async_step_reauth_invalid_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry_added_to_hass),
    _discovered: AsyncMock = Depends(mock_discovered_service_info),
) -> None:
    """Test reauth flow with an invalid key shows error and allows retry."""
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    # Submit wrong key
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCESS_TOKEN: VICTRON_TEST_WRONG_TOKEN},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": "invalid_access_token"})

    # Now submit correct key
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCESS_TOKEN: VICTRON_VEBUS_TOKEN},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def async_step_reauth_device_not_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry_added_to_hass),
) -> None:
    """Test reauth flow when device is not currently broadcasting."""
    # No mock_discovered_service_info, so no devices will be found
    with patch(
        "homeassistant.components.victron_ble.config_flow.async_discovered_service_info",
        return_value=[],
    ):
        result = await config_entry.start_reauth_flow(hass)
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("reauth_confirm")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_ACCESS_TOKEN: VICTRON_VEBUS_TOKEN},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("reauth_confirm")
        expect(result["errors"]).to_equal({"base": "no_devices_found"})


@test
async def reauth_flow_sets_title_placeholders(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry_added_to_hass),
    _discovered: AsyncMock = Depends(mock_discovered_service_info),
) -> None:
    """Test that reauth flow has title_placeholders set for flow_title rendering."""
    await config_entry.start_reauth_flow(hass)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect(flows[0]["context"]["title_placeholders"]["name"]).to_equal(
        config_entry.title
    )
