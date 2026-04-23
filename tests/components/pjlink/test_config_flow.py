"""Test the PJLink config flow."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.pjlink.const import DOMAIN
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .const import DEFAULT_DATA, DEFAULT_DATA_W_ENCODING, DEFAULT_DATA_WO_PORT

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_projector as mock_projector_fx,
    mock_setup_entry as mock_setup_entry_fx,
)


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry_fx),
    _proj: MagicMock = Depends(mock_projector_fx),
) -> None:
    """Wire mock_network, mock_setup_entry, mock_projector for every test."""


@test
async def user_flow_creates_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test that the user flow creates an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], DEFAULT_DATA
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test name")
    expect(result["data"]).to_equal(DEFAULT_DATA)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_flow_aborts_if_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test user flow aborts if already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], DEFAULT_DATA
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("runtime_error", RuntimeError, "invalid_auth"),
    test.case("timeout", TimeoutError, "cannot_connect"),
    test.case("unknown", Exception, "unknown"),
)
async def form_invalid_inputs(
    side_effect: type[Exception],
    error_str: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_projector: MagicMock = Depends(mock_projector_fx),
) -> None:
    """Test we handle invalid inputs."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_instance = mock_projector.from_address.return_value
    mock_instance.authenticate.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], DEFAULT_DATA
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_str})

    mock_instance.authenticate.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], DEFAULT_DATA
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test name")
    expect(result["data"]).to_equal(DEFAULT_DATA)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("default", DEFAULT_DATA),
    test.case("no_port", DEFAULT_DATA_WO_PORT),
    test.case("with_encoding", DEFAULT_DATA_W_ENCODING),
)
async def import_creates_entry(
    import_data: dict[str, Any],
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test importing a YAML config creates an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=import_data
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test name")
    expect(result["data"]).to_equal(DEFAULT_DATA)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def import_aborts_if_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test importing a YAML config aborts if already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=DEFAULT_DATA
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("runtime_error", RuntimeError, "invalid_auth"),
    test.case("timeout", TimeoutError, "cannot_connect"),
    test.case("unknown", Exception, "unknown"),
)
async def import_invalid_inputs(
    side_effect: type[Exception],
    error_str: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_projector: MagicMock = Depends(mock_projector_fx),
) -> None:
    """Test we handle invalid inputs."""
    mock_instance = mock_projector.from_address.return_value
    mock_instance.authenticate.side_effect = side_effect
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=DEFAULT_DATA
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(error_str)
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(0)
