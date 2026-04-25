"""Test the config flow for the Probe Plus."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.probe_plus.const import DOMAIN
from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_IGNORE, SOURCE_USER
from homeassistant.const import CONF_ADDRESS, CONF_MODEL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.bluetooth import BluetoothServiceInfo

from ._fixtures import (
    mock_config_entry as mock_config_entry_fixture,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

service_info = BluetoothServiceInfo(
    name="FM210",
    address="aa:bb:cc:dd:ee:ff",
    rssi=-63,
    manufacturer_data={},
    service_data={},
    service_uuids=[],
    source="local",
)


@fixture
def mock_discovered_service_info() -> Generator[AsyncMock]:
    """Override getting Bluetooth service info."""
    with patch(
        "homeassistant.components.probe_plus.config_flow.async_discovered_service_info",
        return_value=[service_info],
    ) as mock_discovered_service_info:
        yield mock_discovered_service_info


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_config_flow_creates_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _service_info: AsyncMock = Depends(mock_discovered_service_info),
) -> None:
    """Test the user configuration flow successfully creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal("aa:bb:cc:dd:ee:ff")
    expect(result["title"]).to_equal("FM210 aa:bb:cc:dd:ee:ff")
    expect(result["data"]).to_equal(
        {CONF_ADDRESS: "aa:bb:cc:dd:ee:ff", CONF_MODEL: "FM210"}
    )


@test
async def user_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _service_info: AsyncMock = Depends(mock_discovered_service_info),
    config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the user flow aborts when the entry is already configured."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    # This aborts with no devices found as the config flow already checks for
    # existing config entries when validating the discovered devices.
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def bluetooth_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _service_info: AsyncMock = Depends(mock_discovered_service_info),
) -> None:
    """Test we can discover a device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=service_info
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("FM210 aa:bb:cc:dd:ee:ff")
    expect(result["result"].unique_id).to_equal("aa:bb:cc:dd:ee:ff")
    expect(result["data"]).to_equal(
        {CONF_ADDRESS: service_info.address, CONF_MODEL: "FM210"}
    )


@test
async def already_configured_bluetooth_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
) -> None:
    """Ensure configured device is not discovered again."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=service_info
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def no_bluetooth_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    service_info_mock: AsyncMock = Depends(mock_discovered_service_info),
) -> None:
    """Test flow aborts on unsupported device."""
    service_info_mock.return_value = []

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def user_setup_replaces_ignored_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _service_info: AsyncMock = Depends(mock_discovered_service_info),
) -> None:
    """Test the user flow can replace an ignored device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        source=SOURCE_IGNORE,
        data={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    # Verify the ignored device is in the dropdown.
    expect(
        "aa:bb:cc:dd:ee:ff" in result["data_schema"].schema[CONF_ADDRESS].container
    ).to_be(True)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ADDRESS: "aa:bb:cc:dd:ee:ff"},
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["result"].unique_id).to_equal("aa:bb:cc:dd:ee:ff")
    expect(result2["title"]).to_equal("FM210 aa:bb:cc:dd:ee:ff")
    expect(result2["data"]).to_equal(
        {CONF_ADDRESS: "aa:bb:cc:dd:ee:ff", CONF_MODEL: "FM210"}
    )
