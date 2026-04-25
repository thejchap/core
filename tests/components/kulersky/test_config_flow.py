"""Test the Kuler Sky config flow."""

from unittest.mock import AsyncMock, Mock, patch

import pykulersky
from tryke import Depends, expect, fixture, test

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.components.kulersky.config_flow import DOMAIN
from homeassistant.config_entries import (
    SOURCE_BLUETOOTH,
    SOURCE_IGNORE,
    SOURCE_INTEGRATION_DISCOVERY,
    SOURCE_USER,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.bluetooth import generate_advertisement_data, generate_ble_device
from tests.hass_fixtures import (
    enable_bluetooth,
    hass as hass_fixture,
    mock_network,
)

KULERSKY_SERVICE_INFO = BluetoothServiceInfoBleak(
    name="KulerLight",
    manufacturer_data={},
    service_data={},
    service_uuids=["8d96a001-0002-64c2-0001-9acc4838521c"],
    address="AA:BB:CC:DD:EE:FF",
    rssi=-60,
    source="local",
    advertisement=generate_advertisement_data(
        local_name="KulerLight",
        manufacturer_data={},
        service_data={},
        service_uuids=["8d96a001-0002-64c2-0001-9acc4838521c"],
    ),
    device=generate_ble_device("AA:BB:CC:DD:EE:FF", "KulerLight"),
    time=0,
    connectable=True,
    tx_power=-127,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bluetooth: None = Depends(enable_bluetooth),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def bluetooth_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth with a valid device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=KULERSKY_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch("pykulersky.Light", Mock(return_value=AsyncMock())):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: "AA:BB:CC:DD:EE:FF"},
        )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("KulerLight (EEFF)")
    expect(result["data"]).to_equal(
        {
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
        }
    )


@test
async def integration_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth with a valid device."""
    with patch(
        "homeassistant.components.kulersky.config_flow.async_last_service_info",
        return_value=KULERSKY_SERVICE_INFO,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_INTEGRATION_DISCOVERY},
            data={CONF_ADDRESS: "AA:BB:CC:DD:EE:FF"},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("KulerLight (EEFF)")
    expect(result["data"]).to_equal(
        {
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
        }
    )


@test
async def integration_discovery_no_last_service_info(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth with a valid device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_INTEGRATION_DISCOVERY},
        data={CONF_ADDRESS: "AA:BB:CC:DD:EE:FF"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("AA:BB:CC:DD:EE:FF")
    expect(result["data"]).to_equal(
        {
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
        }
    )


@test
async def user_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user manually setting up the integration."""
    with patch(
        "homeassistant.components.kulersky.config_flow.async_discovered_service_info",
        return_value=[
            KULERSKY_SERVICE_INFO,
            KULERSKY_SERVICE_INFO,
        ],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch("pykulersky.Light", Mock(return_value=AsyncMock())):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: "AA:BB:CC:DD:EE:FF"},
        )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("KulerLight (EEFF)")
    expect(result["data"]).to_equal(
        {
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
        }
    )


@test
async def user_setup_no_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user manually setting up the integration."""
    with patch(
        "homeassistant.components.kulersky.config_flow.async_discovered_service_info",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a connection error trying to set up."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=KULERSKY_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch("pykulersky.Light", Mock(side_effect=pykulersky.PykulerskyException)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: "AA:BB:CC:DD:EE:FF"},
        )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("cannot_connect")


@test
async def unexpected_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test an unexpected error trying to set up."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=KULERSKY_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch("pykulersky.Light", Mock(side_effect=Exception)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: "AA:BB:CC:DD:EE:FF"},
        )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("unknown")


@test
async def user_setup_replaces_ignored_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user flow can replace an ignored device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="AA:BB:CC:DD:EE:FF",
        source=SOURCE_IGNORE,
        data={},
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.kulersky.config_flow.async_discovered_service_info",
        return_value=[KULERSKY_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    expect(
        "AA:BB:CC:DD:EE:FF" in result["data_schema"].schema[CONF_ADDRESS].container
    ).to_be(True)

    with patch("pykulersky.Light", Mock(return_value=AsyncMock())):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: "AA:BB:CC:DD:EE:FF"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("KulerLight (EEFF)")
    expect(result2["data"]).to_equal(
        {
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
        }
    )
    expect(result2["result"].unique_id).to_equal("AA:BB:CC:DD:EE:FF")
