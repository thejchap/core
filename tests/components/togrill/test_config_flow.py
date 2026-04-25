"""Test the ToGrill config flow."""

from unittest.mock import AsyncMock, Mock

from bleak.exc import BleakError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.togrill.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import TOGRILL_SERVICE_INFO, TOGRILL_SERVICE_INFO_NO_NAME, setup_entry
from ._fixtures import mock_client, mock_client_class, mock_entry, mock_setup_entry

from tests.common import MockConfigEntry
from tests.components.bluetooth import inject_bluetooth_service_info
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _client: Mock = Depends(mock_client),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def user_selection(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can select a device."""
    inject_bluetooth_service_info(hass, TOGRILL_SERVICE_INFO)
    inject_bluetooth_service_info(hass, TOGRILL_SERVICE_INFO_NO_NAME)
    await hass.async_block_till_done(wait_background_tasks=True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"address": TOGRILL_SERVICE_INFO.address},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "address": TOGRILL_SERVICE_INFO.address,
            "model": "Pro-05",
            "probe_count": 0,
            "has_ambient": False,
        }
    )
    expect(result["title"]).to_equal("Pro-05")
    expect(result["result"].unique_id).to_equal(TOGRILL_SERVICE_INFO.address)


@test
async def user_selection_ignored(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can select a device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TOGRILL_SERVICE_INFO.address,
        source=config_entries.SOURCE_IGNORE,
    )
    entry.add_to_hass(hass)

    inject_bluetooth_service_info(hass, TOGRILL_SERVICE_INFO)
    await hass.async_block_till_done(wait_background_tasks=True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"address": TOGRILL_SERVICE_INFO.address},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def failed_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: Mock = Depends(mock_client),
    client_class: Mock = Depends(mock_client_class),
) -> None:
    """Test failure to connect result."""
    client_class.connect.side_effect = BleakError("Failed to connect")

    inject_bluetooth_service_info(hass, TOGRILL_SERVICE_INFO)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"address": TOGRILL_SERVICE_INFO.address},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("failed_to_read_config")


@test
async def failed_read(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(mock_client),
) -> None:
    """Test failure to read from device."""
    inject_bluetooth_service_info(hass, TOGRILL_SERVICE_INFO)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    client.read.side_effect = BleakError("something went wrong")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"address": TOGRILL_SERVICE_INFO.address},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("failed_to_read_config")


@test
async def no_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test missing device."""
    inject_bluetooth_service_info(hass, TOGRILL_SERVICE_INFO_NO_NAME)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def duplicate_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_entry),
) -> None:
    """Test we can not setup a device again."""
    inject_bluetooth_service_info(hass, TOGRILL_SERVICE_INFO)
    await hass.async_block_till_done(wait_background_tasks=True)

    await setup_entry(hass, entry, [])

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def bluetooth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth device discovery."""
    # Inject the service info will trigger the flow to start.
    inject_bluetooth_service_info(hass, TOGRILL_SERVICE_INFO)
    await hass.async_block_till_done(wait_background_tasks=True)

    result = next(iter(hass.config_entries.flow.async_progress_by_handler(DOMAIN)))

    expect(result["step_id"]).to_equal("bluetooth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "address": TOGRILL_SERVICE_INFO.address,
            "model": "Pro-05",
            "probe_count": 0,
            "has_ambient": False,
        }
    )
    expect(result["title"]).to_equal("Pro-05")
    expect(result["result"].unique_id).to_equal(TOGRILL_SERVICE_INFO.address)
