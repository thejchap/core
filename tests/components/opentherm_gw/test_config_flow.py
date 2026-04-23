"""Test the Opentherm Gateway config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from serial import SerialException
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.opentherm_gw.const import (
    CONF_FLOOR_TEMP,
    CONF_READ_PRECISION,
    CONF_SET_PRECISION,
    CONF_TEMPORARY_OVRD_MODE,
    DOMAIN,
)
from homeassistant.const import (
    CONF_DEVICE,
    CONF_ID,
    CONF_NAME,
    PRECISION_HALVES,
    PRECISION_TENTHS,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import (
    mock_pyotgw as mock_pyotgw_fx,
    mock_setup_entry as mock_setup_entry_fx,
)


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def form_user(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pyotgw: MagicMock = Depends(mock_pyotgw_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_NAME: "Test Entry 1", CONF_DEVICE: "/dev/ttyUSB0"}
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Test Entry 1")
    expect(result2["data"]).to_equal(
        {
            CONF_NAME: "Test Entry 1",
            CONF_DEVICE: "/dev/ttyUSB0",
            CONF_ID: "test_entry_1",
        }
    )
    expect(mock_pyotgw.return_value.connect.await_count).to_equal(1)
    expect(mock_pyotgw.return_value.disconnect.await_count).to_equal(1)


@test
async def form_duplicate_entries(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pyotgw: MagicMock = Depends(mock_pyotgw_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test duplicate device or id errors."""
    flow1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    flow2 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    flow3 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result1 = await hass.config_entries.flow.async_configure(
        flow1["flow_id"], {CONF_NAME: "Test Entry 1", CONF_DEVICE: "/dev/ttyUSB0"}
    )
    expect(result1["type"]).to_be(FlowResultType.CREATE_ENTRY)

    result2 = await hass.config_entries.flow.async_configure(
        flow2["flow_id"], {CONF_NAME: "Test Entry 1", CONF_DEVICE: "/dev/ttyUSB1"}
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "id_exists"})

    result3 = await hass.config_entries.flow.async_configure(
        flow3["flow_id"], {CONF_NAME: "Test Entry 2", CONF_DEVICE: "/dev/ttyUSB0"}
    )
    expect(result3["type"]).to_be(FlowResultType.FORM)
    expect(result3["errors"]).to_equal({"base": "already_configured"})

    expect(mock_pyotgw.return_value.connect.await_count).to_equal(1)
    expect(mock_pyotgw.return_value.disconnect.await_count).to_equal(1)


@test
async def form_connection_timeout(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pyotgw: MagicMock = Depends(mock_pyotgw_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test we handle connection timeout."""
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_pyotgw.return_value.connect.side_effect = TimeoutError

    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"],
        {CONF_NAME: "Test Entry 1", CONF_DEVICE: "socket://192.0.2.254:1234"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "timeout_connect"})

    expect(mock_pyotgw.return_value.connect.await_count).to_equal(1)


@test
async def form_connection_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pyotgw: MagicMock = Depends(mock_pyotgw_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test we handle serial connection error."""
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_pyotgw.return_value.connect.side_effect = SerialException

    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], {CONF_NAME: "Test Entry 1", CONF_DEVICE: "/dev/ttyUSB0"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})
    expect(mock_pyotgw.return_value.connect.await_count).to_equal(1)


@test
async def options_form(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pyotgw: MagicMock = Depends(mock_pyotgw_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test the options form."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Mock Gateway",
        data={
            CONF_NAME: "Mock Gateway",
            CONF_DEVICE: "/dev/null",
            CONF_ID: "mock_gateway",
        },
        options={},
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    flow = await hass.config_entries.options.async_init(
        entry.entry_id, context={"source": "test"}, data=None
    )
    expect(flow["type"]).to_be(FlowResultType.FORM)
    expect(flow["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        user_input={
            CONF_FLOOR_TEMP: True,
            CONF_READ_PRECISION: PRECISION_HALVES,
            CONF_SET_PRECISION: PRECISION_HALVES,
            CONF_TEMPORARY_OVRD_MODE: True,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_READ_PRECISION]).to_equal(PRECISION_HALVES)
    expect(result["data"][CONF_SET_PRECISION]).to_equal(PRECISION_HALVES)
    expect(result["data"][CONF_TEMPORARY_OVRD_MODE]).to_be(True)
    expect(result["data"][CONF_FLOOR_TEMP]).to_be(True)

    flow = await hass.config_entries.options.async_init(
        entry.entry_id, context={"source": "test"}, data=None
    )

    result = await hass.config_entries.options.async_configure(
        flow["flow_id"], user_input={CONF_READ_PRECISION: 0}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_READ_PRECISION]).to_equal(0.0)
    expect(result["data"][CONF_SET_PRECISION]).to_equal(PRECISION_HALVES)
    expect(result["data"][CONF_TEMPORARY_OVRD_MODE]).to_be(True)
    expect(result["data"][CONF_FLOOR_TEMP]).to_be(True)

    flow = await hass.config_entries.options.async_init(
        entry.entry_id, context={"source": "test"}, data=None
    )

    result = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        user_input={
            CONF_FLOOR_TEMP: False,
            CONF_READ_PRECISION: PRECISION_TENTHS,
            CONF_SET_PRECISION: PRECISION_HALVES,
            CONF_TEMPORARY_OVRD_MODE: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_READ_PRECISION]).to_equal(PRECISION_TENTHS)
    expect(result["data"][CONF_SET_PRECISION]).to_equal(PRECISION_HALVES)
    expect(result["data"][CONF_TEMPORARY_OVRD_MODE]).to_be(False)
    expect(result["data"][CONF_FLOOR_TEMP]).to_be(False)
