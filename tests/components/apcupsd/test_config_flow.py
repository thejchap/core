"""Test APCUPSd config flow setup process."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.apcupsd.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import CONF_DATA, MOCK_MINIMAL_STATUS, MOCK_STATUS

from tests.common import MockConfigEntry
from tests.components.apcupsd._fixtures import (
    mock_config_entry,
    mock_request_status,
    mock_setup_entry,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case("oserror", OSError()),
    test.case(
        "incomplete_read",
        asyncio.IncompleteReadError(partial=b"", expected=100),
    ),
    test.case("timeout", TimeoutError()),
)
async def config_flow_cannot_connect(
    exception: Exception,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_request_status: AsyncMock = Depends(mock_request_status),
) -> None:
    """Test config flow setup with a connection error."""
    mock_request_status.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONF_DATA
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]["base"]).to_equal("cannot_connect")


@test
async def config_flow_duplicate_host_port(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_request_status: AsyncMock = Depends(mock_request_status),
) -> None:
    """Test duplicate config flow setup with the same host / port."""
    mock_config_entry.add_to_hass(hass)

    mock_request_status.return_value = MOCK_STATUS
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONF_DATA
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")

    another_host = CONF_DATA | {CONF_HOST: "another_host"}
    mock_request_status.return_value = MOCK_STATUS | {
        "SERIALNO": MOCK_STATUS["SERIALNO"] + "ZZZ"
    }
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=another_host,
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["data"]).to_equal(another_host)


@test
async def config_flow_duplicate_serial_number(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_request_status: AsyncMock = Depends(mock_request_status),
) -> None:
    """Test duplicate config flow setup with different host but the same serial number."""
    mock_config_entry.add_to_hass(hass)

    mock_request_status.return_value = MOCK_STATUS
    another_host = CONF_DATA | {CONF_HOST: "another_host"}
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=another_host,
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")

    mock_request_status.return_value = MOCK_STATUS | {
        "SERIALNO": MOCK_STATUS["SERIALNO"] + "ZZZ"
    }
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=another_host
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["data"]).to_equal(another_host)


@test
async def flow_works(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_request_status: AsyncMock = Depends(mock_request_status),
) -> None:
    """Test successful creation of config entries via user configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=CONF_DATA
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(MOCK_STATUS["UPSNAME"])
    expect(result["data"]).to_equal(CONF_DATA)
    expect(result["result"].unique_id).to_equal(MOCK_STATUS["SERIALNO"])

    mock_setup_entry.assert_called_once()


@test.cases(
    test.case(
        "friendly_name",
        MOCK_MINIMAL_STATUS | {"UPSNAME": "Friendly Name"},
        "Friendly Name",
    ),
    test.case(
        "model_x",
        MOCK_MINIMAL_STATUS | {"MODEL": "MODEL X"},
        "MODEL X",
    ),
    test.case(
        "serialno_zzzz",
        MOCK_MINIMAL_STATUS | {"SERIALNO": "ZZZZ"},
        "ZZZZ",
    ),
    test.case(
        "serialno_blank",
        MOCK_MINIMAL_STATUS | {"SERIALNO": "Blank"},
        "APC UPS",
    ),
    test.case(
        "minimal",
        MOCK_MINIMAL_STATUS | {},
        "APC UPS",
    ),
)
async def flow_minimal_status(
    status_override: dict[str, Any],
    expected_title: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_request_status: AsyncMock = Depends(mock_request_status),
) -> None:
    """Test creation with minimal status reported; title varies by fields."""
    mock_request_status.return_value = status_override
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data=CONF_DATA
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["data"]).to_equal(CONF_DATA)
    expect(result["title"]).to_equal(expected_title)
    mock_setup_entry.assert_called_once()


@test
async def reconfigure_flow_works(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_request_status: AsyncMock = Depends(mock_request_status),
) -> None:
    """Test successful reconfiguration of an existing entry."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reconfigure")

    new_conf_data = {CONF_HOST: "new_host", CONF_PORT: 4321}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=new_conf_data
    )
    await hass.async_block_till_done()
    mock_setup_entry.assert_called_once()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reconfigure_successful")

    expect(mock_config_entry.data[CONF_HOST]).to_equal(new_conf_data[CONF_HOST])
    expect(mock_config_entry.data[CONF_PORT]).to_equal(new_conf_data[CONF_PORT])


@test
async def reconfigure_flow_cannot_connect(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_request_status: AsyncMock = Depends(mock_request_status),
) -> None:
    """Test reconfiguration with connection error and recovery."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reconfigure")

    new_conf_data = {CONF_HOST: "new_host", CONF_PORT: 4321}
    mock_request_status.side_effect = OSError()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=new_conf_data
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]["base"]).to_equal("cannot_connect")

    mock_request_status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=new_conf_data
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(mock_config_entry.data).to_equal(new_conf_data)


@test.cases(
    test.case("unset_to_serial", None, MOCK_STATUS["SERIALNO"]),
    test.case("serial_to_blank", MOCK_STATUS["SERIALNO"], "Blank"),
    test.case(
        "serial_to_different",
        MOCK_STATUS["SERIALNO"],
        MOCK_STATUS["SERIALNO"] + "ZZZ",
    ),
)
async def reconfigure_flow_wrong_device(
    unique_id_before: str | None,
    unique_id_after: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_request_status: AsyncMock = Depends(mock_request_status),
) -> None:
    """Test reconfiguration with a different device (wrong serial number)."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, unique_id=unique_id_before
    )

    result = await mock_config_entry.start_reconfigure_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_request_status.return_value = MOCK_STATUS | {"SERIALNO": unique_id_after}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "new_host", CONF_PORT: 4321}
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("wrong_apcupsd_daemon")
