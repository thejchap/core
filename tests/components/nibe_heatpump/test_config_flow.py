"""Test the Nibe Heat Pump config flow."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock

from nibe.exceptions import (
    AddressInUseException,
    CoilNotFoundException,
    ReadException,
    ReadSendException,
    WriteException,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.nibe_heatpump import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.nibe_heatpump._fixtures import (
    coils,
    mock_connection,
    mock_connection_construct,
    mock_setup_entry,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_FLOW_NIBEGW_USERDATA = {
    "model": "F1155",
    "ip_address": "127.0.0.1",
    "listening_port": 9999,
    "remote_read_port": 10000,
    "remote_write_port": 10001,
}


MOCK_FLOW_MODBUS_USERDATA = {
    "model": "S1155",
    "modbus_url": "tcp://127.0.0.1",
    "modbus_unit": 0,
}


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _mse: AsyncMock = Depends(mock_setup_entry),
    _mcc: Mock = Depends(mock_connection_construct),
    _mc: AsyncMock = Depends(mock_connection),
) -> None:
    """Wire mocks for every test (autouse parity)."""


async def _get_connection_form(
    hass: HomeAssistant, connection_type: str
) -> config_entries.ConfigFlowResult:
    """Helper to produce the connection-type form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.MENU)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": connection_type}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)
    return result


@test
async def nibegw_form(
    hass: HomeAssistant = Depends(hass_fixture),
    coils_: dict[int, Any] = Depends(coils),
    mock_setup: Mock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await _get_connection_form(hass, "nibegw")

    coils_[48852] = 1

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_FLOW_NIBEGW_USERDATA
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("F1155 at 127.0.0.1")
    expect(result2["data"]).to_equal(
        {
            "model": "F1155",
            "ip_address": "127.0.0.1",
            "listening_port": 9999,
            "remote_read_port": 10000,
            "remote_write_port": 10001,
            "word_swap": True,
            "connection_type": "nibegw",
        }
    )
    expect(len(mock_setup.mock_calls)).to_equal(1)


@test
async def modbus_form(
    hass: HomeAssistant = Depends(hass_fixture),
    coils_: dict[int, Any] = Depends(coils),
    mock_setup: Mock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await _get_connection_form(hass, "modbus")

    coils_[40022] = 1

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_FLOW_MODBUS_USERDATA
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("S1155 at 127.0.0.1")
    expect(result2["data"]).to_equal(
        {
            "model": "S1155",
            "modbus_url": "tcp://127.0.0.1",
            "modbus_unit": 0,
            "connection_type": "modbus",
        }
    )
    expect(len(mock_setup.mock_calls)).to_equal(1)


@test
async def modbus_invalid_url(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_conn_ctor: Mock = Depends(mock_connection_construct),
) -> None:
    """Test we handle invalid auth."""
    result = await _get_connection_form(hass, "modbus")

    mock_conn_ctor.side_effect = ValueError()
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {**MOCK_FLOW_MODBUS_USERDATA, "modbus_url": "invalid://url"},
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"modbus_url": "url"})


@test
async def nibegw_address_inuse(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_conn: Mock = Depends(mock_connection),
) -> None:
    """Test we handle invalid auth."""
    result = await _get_connection_form(hass, "nibegw")

    mock_conn.start = AsyncMock()
    mock_conn.start.side_effect = AddressInUseException()

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_FLOW_NIBEGW_USERDATA
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"listening_port": "address_in_use"})

    mock_conn.start.side_effect = Exception()

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_FLOW_NIBEGW_USERDATA
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test.cases(
    test.case("nibegw", "nibegw", MOCK_FLOW_NIBEGW_USERDATA),
    test.case("modbus", "modbus", MOCK_FLOW_MODBUS_USERDATA),
)
async def read_timeout(
    connection_type: str,
    data: dict,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_conn: Mock = Depends(mock_connection),
) -> None:
    """Test we handle cannot connect error."""
    result = await _get_connection_form(hass, connection_type)

    mock_conn.verify_connectivity.side_effect = ReadException()

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "read"})


@test.cases(
    test.case("nibegw", "nibegw", MOCK_FLOW_NIBEGW_USERDATA),
    test.case("modbus", "modbus", MOCK_FLOW_MODBUS_USERDATA),
)
async def write_timeout(
    connection_type: str,
    data: dict,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_conn: Mock = Depends(mock_connection),
) -> None:
    """Test we handle cannot connect error."""
    result = await _get_connection_form(hass, connection_type)

    mock_conn.verify_connectivity.side_effect = WriteException()

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "write"})


@test.cases(
    test.case("nibegw", "nibegw", MOCK_FLOW_NIBEGW_USERDATA),
    test.case("modbus", "modbus", MOCK_FLOW_MODBUS_USERDATA),
)
async def unexpected_exception(
    connection_type: str,
    data: dict,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_conn: Mock = Depends(mock_connection),
) -> None:
    """Test we handle cannot connect error."""
    result = await _get_connection_form(hass, connection_type)

    mock_conn.verify_connectivity.side_effect = Exception()

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test.cases(
    test.case("nibegw", "nibegw", MOCK_FLOW_NIBEGW_USERDATA),
    test.case("modbus", "modbus", MOCK_FLOW_MODBUS_USERDATA),
)
async def nibegw_invalid_host(
    connection_type: str,
    data: dict,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_conn: Mock = Depends(mock_connection),
) -> None:
    """Test we handle cannot connect error."""
    result = await _get_connection_form(hass, connection_type)

    mock_conn.verify_connectivity.side_effect = ReadSendException()

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    expect(result2["type"]).to_be(FlowResultType.FORM)
    if connection_type == "nibegw":
        expect(result2["errors"]).to_equal({"ip_address": "address"})
    else:
        expect(result2["errors"]).to_equal({"modbus_url": "address"})


@test.cases(
    test.case("nibegw", "nibegw", MOCK_FLOW_NIBEGW_USERDATA),
    test.case("modbus", "modbus", MOCK_FLOW_MODBUS_USERDATA),
)
async def model_missing_coil(
    connection_type: str,
    data: dict,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_conn: Mock = Depends(mock_connection),
) -> None:
    """Test we handle cannot connect error."""
    result = await _get_connection_form(hass, connection_type)

    mock_conn.verify_connectivity.side_effect = CoilNotFoundException()

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "model"})
