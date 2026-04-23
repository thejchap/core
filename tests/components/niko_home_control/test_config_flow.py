"""Test niko_home_control config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.niko_home_control.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.niko_home_control._fixtures import (
    mock_config_entry,
    mock_niko_home_control_connection,
    mock_setup_entry,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _conn: AsyncMock = Depends(mock_niko_home_control_connection),
    mock_setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.0.123"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Niko Home Control")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.0.123"})
    expect(len(mock_setup.mock_calls)).to_equal(1)


@test.cases(
    test.case("timeout", TimeoutError, "timeout_connect"),
    test.case("os_error", OSError, "cannot_connect"),
    test.case("unknown", Exception, "unknown"),
)
async def flow_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    conn: AsyncMock = Depends(mock_niko_home_control_connection),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the timeout error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    conn.connect.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.0.123"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    conn.connect.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.0.123"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def duplicate_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test uniqueness."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.0.123"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def duplicate_reconfigure_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    _conn: AsyncMock = Depends(mock_niko_home_control_connection),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure to other existing entry."""
    config_entry.add_to_hass(hass)
    another_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Niko Home Control",
        data={CONF_HOST: "192.168.0.124"},
        entry_id="01JFN93M7KRA38V5AMPCJ2JYYB",
    )
    another_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.0.124"}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reconfigure(
    hass: HomeAssistant = Depends(hass_fixture),
    _conn: AsyncMock = Depends(mock_niko_home_control_connection),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the reconfigure flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(set(result["data_schema"].schema)).to_equal({CONF_HOST})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.0.122"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")


@test.cases(
    test.case("timeout", TimeoutError, "timeout_connect"),
    test.case("os_error", OSError, "cannot_connect"),
    test.case("unknown", Exception, "unknown"),
)
async def reconfigure_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    conn: AsyncMock = Depends(mock_niko_home_control_connection),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfiguration with connection error."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    conn.connect.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.0.122"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    conn.connect.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.0.122"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
