"""Test the acaia config flow."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from aioacaia.exceptions import AcaiaDeviceNotFound, AcaiaError, AcaiaUnknownDevice
from tryke import Depends, expect, fixture, test

from homeassistant.components.acaia.const import CONF_IS_NEW_STYLE_SCALE, DOMAIN
from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_USER
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.bluetooth import BluetoothServiceInfo

from tests.common import MockConfigEntry
from tests.components.acaia._fixtures import (
    mock_config_entry,
    mock_setup_entry,
    mock_verify,
)
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


service_info = BluetoothServiceInfo(
    name="LUNAR-DDEEFF",
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
        "homeassistant.components.acaia.config_flow.async_discovered_service_info",
        return_value=[service_info],
    ) as mock_discovered_service_info:
        yield mock_discovered_service_info


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_verify: AsyncMock = Depends(mock_verify),
    _mock_discovered_service_info: AsyncMock = Depends(mock_discovered_service_info),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    user_input = {CONF_ADDRESS: "aa:bb:cc:dd:ee:ff"}
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=user_input,
    )

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal("LUNAR-DDEEFF")
    expect(result2["data"]).to_equal({**user_input, CONF_IS_NEW_STYLE_SCALE: True})


@test
async def bluetooth_discovery(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_verify: AsyncMock = Depends(mock_verify),
) -> None:
    """Test we can discover a device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=service_info
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal(service_info.name)
    expect(result2["data"]).to_equal(
        {CONF_ADDRESS: service_info.address, CONF_IS_NEW_STYLE_SCALE: True}
    )


@test.cases(
    test.case("device_not_found", AcaiaDeviceNotFound("Error"), "device_not_found"),
    test.case("unknown", AcaiaError(), "unknown"),
    test.case("unsupported_device", AcaiaUnknownDevice(), "unsupported_device"),
)
async def bluetooth_discovery_errors(
    exception: Exception,
    error: str,
    hass: HomeAssistant = Depends(hass),
    mock_verify: AsyncMock = Depends(mock_verify),
) -> None:
    """Test abortions of Bluetooth discovery."""
    mock_verify.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=service_info
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal(error)


@test
async def already_configured(
    hass: HomeAssistant = Depends(hass),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_verify: AsyncMock = Depends(mock_verify),
    _mock_discovered_service_info: AsyncMock = Depends(mock_discovered_service_info),
) -> None:
    """Ensure we can't add the same device twice."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ADDRESS: "aa:bb:cc:dd:ee:ff"},
    )
    await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.ABORT).to_be(True)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def already_configured_bluetooth_discovery(
    hass: HomeAssistant = Depends(hass),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Ensure configure device is not discovered again."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=service_info
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("device_not_found", AcaiaDeviceNotFound("Error"), "device_not_found"),
    test.case("unknown", AcaiaError(), "unknown"),
)
async def recoverable_config_flow_errors(
    exception: Exception,
    error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_verify: AsyncMock = Depends(mock_verify),
    _mock_discovered_service_info: AsyncMock = Depends(mock_discovered_service_info),
) -> None:
    """Test recoverable errors."""
    mock_verify.side_effect = exception
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ADDRESS: "aa:bb:cc:dd:ee:ff"},
    )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": error})

    mock_verify.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {CONF_ADDRESS: "aa:bb:cc:dd:ee:ff"},
    )
    expect(result3["type"] is FlowResultType.CREATE_ENTRY).to_be(True)


@test
async def unsupported_device(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_verify: AsyncMock = Depends(mock_verify),
    _mock_discovered_service_info: AsyncMock = Depends(mock_discovered_service_info),
) -> None:
    """Test flow aborts on unsupported device."""
    mock_verify.side_effect = AcaiaUnknownDevice
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ADDRESS: "aa:bb:cc:dd:ee:ff"},
    )

    expect(result2["type"] is FlowResultType.ABORT).to_be(True)
    expect(result2["reason"]).to_equal("unsupported_device")


@test
async def no_bluetooth_devices(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_discovered_service_info: AsyncMock = Depends(mock_discovered_service_info),
) -> None:
    """Test flow aborts on unsupported device."""
    mock_discovered_service_info.return_value = []

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("no_devices_found")
