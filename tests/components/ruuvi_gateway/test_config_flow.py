"""Test the Ruuvi Gateway config flow."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from aioruuvigateway.excs import CannotConnect, InvalidAuth
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.ruuvi_gateway.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from ._fixtures import mock_bluetooth

from .consts import (
    BASE_DATA,
    EXPECTED_TITLE,
    GATEWAY_MAC_LOWER,
    GET_GATEWAY_HISTORY_DATA,
)
from .utils import patch_gateway_ok, patch_setup_entry_ok

from tests.hass_fixtures import hass as hass_fixture

DHCP_IP = "1.2.3.4"
DHCP_DATA = {**BASE_DATA, "host": DHCP_IP}


@fixture
async def _trigger_executor(
    _bt: None = Depends(mock_bluetooth),
) -> None:
    """Wire autouse mock_bluetooth."""


@test.cases(
    test.case(
        "user",
        init_data=None,
        init_context={"source": config_entries.SOURCE_USER},
        entry=BASE_DATA,
    ),
    test.case(
        "dhcp",
        init_data=DhcpServiceInfo(
            hostname="RuuviGateway1234",
            ip=DHCP_IP,
            macaddress="1234567890ab",
        ),
        init_context={"source": config_entries.SOURCE_DHCP},
        entry=DHCP_DATA,
    ),
)
async def ok_setup(
    init_data: DhcpServiceInfo | None,
    init_context: dict[str, Any],
    entry: dict[str, Any],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    init_result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=init_data,
        context=init_context,
    )
    expect(init_result["type"]).to_be(FlowResultType.FORM)
    expect(init_result["step_id"]).to_equal(config_entries.SOURCE_USER)
    expect(init_result["errors"]).to_be(None)

    with patch_gateway_ok(), patch_setup_entry_ok() as mock_setup_entry:
        config_result = await hass.config_entries.flow.async_configure(
            init_result["flow_id"],
            entry,
        )
        await hass.async_block_till_done()
    expect(config_result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_result["title"]).to_equal(EXPECTED_TITLE)
    expect(config_result["data"]).to_equal(entry)
    expect(config_result["context"]["unique_id"]).to_equal(GATEWAY_MAC_LOWER)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth."""
    init_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(GET_GATEWAY_HISTORY_DATA, side_effect=InvalidAuth):
        config_result = await hass.config_entries.flow.async_configure(
            init_result["flow_id"],
            BASE_DATA,
        )

    expect(config_result["type"]).to_be(FlowResultType.FORM)
    expect(config_result["errors"]).to_equal({"base": "invalid_auth"})

    with patch_gateway_ok(), patch_setup_entry_ok() as mock_setup_entry:
        config_result = await hass.config_entries.flow.async_configure(
            init_result["flow_id"],
            BASE_DATA,
        )
        await hass.async_block_till_done()
    expect(config_result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_result["title"]).to_equal(EXPECTED_TITLE)
    expect(config_result["data"]).to_equal(BASE_DATA)
    expect(config_result["context"]["unique_id"]).to_equal(GATEWAY_MAC_LOWER)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    init_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(GET_GATEWAY_HISTORY_DATA, side_effect=CannotConnect):
        config_result = await hass.config_entries.flow.async_configure(
            init_result["flow_id"],
            BASE_DATA,
        )

    expect(config_result["type"]).to_be(FlowResultType.FORM)
    expect(config_result["errors"]).to_equal({"base": "cannot_connect"})

    with patch_gateway_ok(), patch_setup_entry_ok() as mock_setup_entry:
        config_result = await hass.config_entries.flow.async_configure(
            init_result["flow_id"],
            BASE_DATA,
        )
        await hass.async_block_till_done()
    expect(config_result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_result["title"]).to_equal(EXPECTED_TITLE)
    expect(config_result["data"]).to_equal(BASE_DATA)
    expect(config_result["context"]["unique_id"]).to_equal(GATEWAY_MAC_LOWER)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_unexpected(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle unexpected errors."""
    init_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(GET_GATEWAY_HISTORY_DATA, side_effect=MemoryError):
        config_result = await hass.config_entries.flow.async_configure(
            init_result["flow_id"],
            BASE_DATA,
        )

    expect(config_result["type"]).to_be(FlowResultType.FORM)
    expect(config_result["errors"]).to_equal({"base": "unknown"})

    with patch_gateway_ok(), patch_setup_entry_ok() as mock_setup_entry:
        config_result = await hass.config_entries.flow.async_configure(
            init_result["flow_id"],
            BASE_DATA,
        )
        await hass.async_block_till_done()
    expect(config_result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_result["title"]).to_equal(EXPECTED_TITLE)
    expect(config_result["data"]).to_equal(BASE_DATA)
    expect(config_result["context"]["unique_id"]).to_equal(GATEWAY_MAC_LOWER)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
