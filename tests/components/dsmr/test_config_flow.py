"""Test the DSMR config flow."""

from itertools import chain, repeat
from typing import Any
from unittest.mock import DEFAULT, AsyncMock, MagicMock, patch

import serial
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.dsmr.const import DOMAIN
from homeassistant.components.usb import SerialDevice
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    dsmr_connection_send_validate_fixture,
    rfxtrx_dsmr_connection_send_validate_fixture,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

SERIAL_DATA = {"serial_id": "12345678", "serial_id_gas": "123456789"}
SERIAL_DATA_SWEDEN = {"serial_id": None, "serial_id_gas": None}


def com_port() -> SerialDevice:
    """Mock of a serial port."""
    return SerialDevice(
        device="/dev/ttyUSB1234",
        serial_number="1234",
        manufacturer="Virtual serial port",
        description="Some serial port",
    )


@fixture
def com_mock() -> MagicMock:
    """Mock the usb scan_serial_ports helper."""
    with patch(
        "homeassistant.components.dsmr.config_flow.usb.async_scan_serial_ports",
        return_value=[com_port()],
    ) as mock:
        yield mock


@test
async def setup_network(
    hass: HomeAssistant = Depends(hass_fixture),
    dsmr_connection_send_validate: tuple[MagicMock, MagicMock, MagicMock] = Depends(
        dsmr_connection_send_validate_fixture
    ),
) -> None:
    """Test we can setup network."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"type": "Network"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("setup_network")
    expect(result["errors"]).to_equal({})

    with patch("homeassistant.components.dsmr.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "10.10.0.1",
                "port": 1234,
                "dsmr_version": "2.2",
            },
        )
        await hass.async_block_till_done()

    entry_data = {
        "host": "10.10.0.1",
        "port": 1234,
        "dsmr_version": "2.2",
        "protocol": "dsmr_protocol",
    }

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("10.10.0.1:1234")
    expect(result["data"]).to_equal({**entry_data, **SERIAL_DATA})


@test
async def setup_network_rfxtrx(
    hass: HomeAssistant = Depends(hass_fixture),
    dsmr_connection_send_validate: tuple[MagicMock, MagicMock, MagicMock] = Depends(
        dsmr_connection_send_validate_fixture
    ),
    rfxtrx_dsmr_connection_send_validate: tuple[
        MagicMock, MagicMock, MagicMock
    ] = Depends(rfxtrx_dsmr_connection_send_validate_fixture),
) -> None:
    """Test we can setup network."""
    (_connection_factory, _transport, protocol) = dsmr_connection_send_validate

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"type": "Network"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("setup_network")
    expect(result["errors"]).to_equal({})

    # set-up DSMRProtocol to yield no valid telegram, this will retry with RFXtrxDSMRProtocol
    protocol.telegram = {}

    with patch("homeassistant.components.dsmr.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "10.10.0.1",
                "port": 1234,
                "dsmr_version": "2.2",
            },
        )
        await hass.async_block_till_done()

    entry_data = {
        "host": "10.10.0.1",
        "port": 1234,
        "dsmr_version": "2.2",
        "protocol": "rfxtrx_dsmr_protocol",
    }

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("10.10.0.1:1234")
    expect(result["data"]).to_equal({**entry_data, **SERIAL_DATA})


@test.cases(
    test.case(
        "v2_2",
        version="2.2",
        entry_data={
            "port": "/dev/ttyUSB1234",
            "dsmr_version": "2.2",
            "protocol": "dsmr_protocol",
            "serial_id": "12345678",
            "serial_id_gas": "123456789",
        },
    ),
    test.case(
        "v5B",
        version="5B",
        entry_data={
            "port": "/dev/ttyUSB1234",
            "dsmr_version": "5B",
            "protocol": "dsmr_protocol",
            "serial_id": "12345678",
            "serial_id_gas": "123456789",
        },
    ),
    test.case(
        "v5L",
        version="5L",
        entry_data={
            "port": "/dev/ttyUSB1234",
            "dsmr_version": "5L",
            "protocol": "dsmr_protocol",
            "serial_id": "12345678",
            "serial_id_gas": "123456789",
        },
    ),
    test.case(
        "v5EONHU",
        version="5EONHU",
        entry_data={
            "port": "/dev/ttyUSB1234",
            "dsmr_version": "5EONHU",
            "protocol": "dsmr_protocol",
            "serial_id": "12345678",
            "serial_id_gas": None,
        },
    ),
    test.case(
        "v5S",
        version="5S",
        entry_data={
            "port": "/dev/ttyUSB1234",
            "dsmr_version": "5S",
            "protocol": "dsmr_protocol",
            "serial_id": None,
            "serial_id_gas": None,
        },
    ),
    test.case(
        "Q3D",
        version="Q3D",
        entry_data={
            "port": "/dev/ttyUSB1234",
            "dsmr_version": "Q3D",
            "protocol": "dsmr_protocol",
            "serial_id": "12345678",
            "serial_id_gas": None,
        },
    ),
)
async def setup_serial(
    version: str,
    entry_data: dict[str, Any],
    _com_mock: MagicMock = Depends(com_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    dsmr_connection_send_validate: tuple[MagicMock, MagicMock, MagicMock] = Depends(
        dsmr_connection_send_validate_fixture
    ),
) -> None:
    """Test we can setup serial."""
    port = com_port()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"type": "Serial"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("setup_serial")
    expect(result["errors"]).to_equal({})

    with patch("homeassistant.components.dsmr.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"port": port.device, "dsmr_version": version},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(port.device)
    expect(result["data"]).to_equal(entry_data)


@test
async def setup_serial_rfxtrx(
    _com_mock: MagicMock = Depends(com_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    dsmr_connection_send_validate: tuple[MagicMock, MagicMock, MagicMock] = Depends(
        dsmr_connection_send_validate_fixture
    ),
    rfxtrx_dsmr_connection_send_validate: tuple[
        MagicMock, MagicMock, MagicMock
    ] = Depends(rfxtrx_dsmr_connection_send_validate_fixture),
) -> None:
    """Test we can setup serial."""
    (_connection_factory, _transport, protocol) = dsmr_connection_send_validate

    port = com_port()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"type": "Serial"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("setup_serial")
    expect(result["errors"]).to_equal({})

    # set-up DSMRProtocol to yield no valid telegram, this will retry with RFXtrxDSMRProtocol
    protocol.telegram = {}

    with patch("homeassistant.components.dsmr.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"port": port.device, "dsmr_version": "2.2"},
        )
        await hass.async_block_till_done()

    entry_data = {
        "port": port.device,
        "dsmr_version": "2.2",
        "protocol": "rfxtrx_dsmr_protocol",
    }

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(port.device)
    expect(result["data"]).to_equal({**entry_data, **SERIAL_DATA})


@test
async def setup_serial_manual(
    _com_mock: MagicMock = Depends(com_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    dsmr_connection_send_validate: tuple[MagicMock, MagicMock, MagicMock] = Depends(
        dsmr_connection_send_validate_fixture
    ),
) -> None:
    """Test we can setup serial with manual entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"type": "Serial"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("setup_serial")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"port": "Enter Manually", "dsmr_version": "2.2"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("setup_serial_manual_path")
    expect(result["errors"]).to_be(None)

    with patch("homeassistant.components.dsmr.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"port": "/dev/ttyUSB0"}
        )
        await hass.async_block_till_done()

    entry_data = {
        "port": "/dev/ttyUSB0",
        "dsmr_version": "2.2",
        "protocol": "dsmr_protocol",
    }

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("/dev/ttyUSB0")
    expect(result["data"]).to_equal({**entry_data, **SERIAL_DATA})


@test
async def setup_serial_fail(
    _com_mock: MagicMock = Depends(com_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    dsmr_connection_send_validate: tuple[MagicMock, MagicMock, MagicMock] = Depends(
        dsmr_connection_send_validate_fixture
    ),
) -> None:
    """Test failed serial connection."""
    (_connection_factory, transport, protocol) = dsmr_connection_send_validate

    port = com_port()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # override the mock to have it fail the first time and succeed after
    first_fail_connection_factory = AsyncMock(
        return_value=(transport, protocol),
        side_effect=chain([serial.SerialException], repeat(DEFAULT)),
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"type": "Serial"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("setup_serial")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.dsmr.config_flow.create_dsmr_reader",
        first_fail_connection_factory,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"port": port.device, "dsmr_version": "2.2"},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("setup_serial")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def setup_serial_timeout(
    _com_mock: MagicMock = Depends(com_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    dsmr_connection_send_validate: tuple[MagicMock, MagicMock, MagicMock] = Depends(
        dsmr_connection_send_validate_fixture
    ),
    rfxtrx_dsmr_connection_send_validate: tuple[
        MagicMock, MagicMock, MagicMock
    ] = Depends(rfxtrx_dsmr_connection_send_validate_fixture),
) -> None:
    """Test failed serial connection."""
    (_connection_factory, _transport, protocol) = dsmr_connection_send_validate
    (
        _connection_factory,
        _transport,
        rfxtrx_protocol,
    ) = rfxtrx_dsmr_connection_send_validate

    port = com_port()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    first_timeout_wait_closed = AsyncMock(
        return_value=True,
        side_effect=chain([TimeoutError], repeat(DEFAULT)),
    )
    protocol.wait_closed = first_timeout_wait_closed

    first_timeout_wait_closed = AsyncMock(
        return_value=True,
        side_effect=chain([TimeoutError], repeat(DEFAULT)),
    )
    rfxtrx_protocol.wait_closed = first_timeout_wait_closed

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"type": "Serial"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("setup_serial")
    expect(result["errors"]).to_equal({})

    with patch("homeassistant.components.dsmr.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"port": port.device, "dsmr_version": "2.2"}
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("setup_serial")
    expect(result["errors"]).to_equal({"base": "cannot_communicate"})


@test
async def setup_serial_wrong_telegram(
    _com_mock: MagicMock = Depends(com_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    dsmr_connection_send_validate: tuple[MagicMock, MagicMock, MagicMock] = Depends(
        dsmr_connection_send_validate_fixture
    ),
    rfxtrx_dsmr_connection_send_validate: tuple[
        MagicMock, MagicMock, MagicMock
    ] = Depends(rfxtrx_dsmr_connection_send_validate_fixture),
) -> None:
    """Test failed telegram data."""
    (_connection_factory, _transport, protocol) = dsmr_connection_send_validate
    (
        _rfxtrx_connection_factory,
        _transport,
        rfxtrx_protocol,
    ) = rfxtrx_dsmr_connection_send_validate

    port = com_port()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"type": "Serial"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("setup_serial")
    expect(result["errors"]).to_equal({})

    protocol.telegram = {}
    rfxtrx_protocol.telegram = {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"port": port.device, "dsmr_version": "2.2"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("setup_serial")
    expect(result["errors"]).to_equal({"base": "cannot_communicate"})


@test
async def options_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test options flow."""

    entry_data = {
        "port": "/dev/ttyUSB0",
        "dsmr_version": "2.2",
    }

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=entry_data,
        unique_id="/dev/ttyUSB0",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "time_between_update": 15,
        },
    )

    with (
        patch("homeassistant.components.dsmr.async_setup_entry", return_value=True),
        patch("homeassistant.components.dsmr.async_unload_entry", return_value=True),
    ):
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

        await hass.async_block_till_done()

    expect(entry.options).to_equal({"time_between_update": 15})
