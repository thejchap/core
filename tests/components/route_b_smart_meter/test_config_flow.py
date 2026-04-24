"""Test the Smart Meter B-route config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

from momonga import MomongaSkJoinFailure, MomongaSkScanFailure
from tryke import Depends, expect, fixture, test

from homeassistant.components.route_b_smart_meter.const import DOMAIN, ENTRY_TITLE
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_DEVICE, CONF_ID, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_momonga, mock_serial_ports, mock_setup_entry, user_input

from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor(
    _setup: AsyncMock = Depends(mock_setup_entry),
    _serial: AsyncMock = Depends(mock_serial_ports),
    _momonga: Mock = Depends(mock_momonga),
) -> None:
    """Wire module-wide fixtures."""


@test
async def step_user_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    serial_ports: AsyncMock = Depends(mock_serial_ports),
    momonga: Mock = Depends(mock_momonga),
    user_in: dict[str, str] = Depends(user_input),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_in,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(ENTRY_TITLE)
    expect(result["data"]).to_equal(user_in)
    expect(result["result"].unique_id).to_equal(user_in[CONF_ID])
    setup_entry.assert_called_once()
    serial_ports.assert_called()
    momonga.assert_called_once_with(
        dev=user_in[CONF_DEVICE],
        rbid=user_in[CONF_ID],
        pwd=user_in[CONF_PASSWORD],
    )


@test.cases(
    test.case("invalid_auth", error=MomongaSkJoinFailure, message="invalid_auth"),
    test.case("cannot_connect", error=MomongaSkScanFailure, message="cannot_connect"),
    test.case("unknown", error=Exception, message="unknown"),
)
async def step_user_form_errors(
    error: type[Exception],
    message: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    serial_ports: AsyncMock = Depends(mock_serial_ports),
    momonga: Mock = Depends(mock_momonga),
    user_in: dict[str, str] = Depends(user_input),
) -> None:
    """Test we handle error."""
    result_init = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    momonga.side_effect = error
    result_configure = await hass.config_entries.flow.async_configure(
        result_init["flow_id"],
        user_in,
    )

    expect(result_configure["type"]).to_be(FlowResultType.FORM)
    expect(result_configure["errors"]).to_equal({"base": message})
    await hass.async_block_till_done()
    serial_ports.assert_called()
    momonga.assert_called_once_with(
        dev=user_in[CONF_DEVICE],
        rbid=user_in[CONF_ID],
        pwd=user_in[CONF_PASSWORD],
    )

    momonga.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result_configure["flow_id"],
        user_in,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(ENTRY_TITLE)
    expect(result["data"]).to_equal(user_in)
