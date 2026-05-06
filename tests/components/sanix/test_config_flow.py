"""Define tests for the Sanix config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from sanix.exceptions import SanixException, SanixInvalidAuthException
from tryke import Depends, expect, fixture, test

from homeassistant.components.sanix.const import (
    CONF_SERIAL_NUMBER,
    DOMAIN,
    MANUFACTURER,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_sanix, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

CONFIG = {CONF_SERIAL_NUMBER: "1810088", CONF_TOKEN: "75868dcf8ea4c64e2063f6c4e70132d2"}


@fixture
def _trigger_executor() -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    sanix: MagicMock = Depends(mock_sanix),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the user step works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        CONFIG,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MANUFACTURER)
    expect(result["data"]).to_equal(
        {
            CONF_SERIAL_NUMBER: "1810088",
            CONF_TOKEN: "75868dcf8ea4c64e2063f6c4e70132d2",
        }
    )

    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "invalid_auth",
        exception=SanixInvalidAuthException("Invalid auth"),
        error="invalid_auth",
    ),
    test.case(
        "unknown",
        exception=SanixException("Something went wrong"),
        error="unknown",
    ),
)
async def form_exceptions(
    exception: Exception,
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    sanix: MagicMock = Depends(mock_sanix),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test Form exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    sanix.return_value.fetch_data.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        CONFIG,
    )

    sanix.return_value.fetch_data.side_effect = None

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        CONFIG,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Sanix")
    expect(result["data"]).to_equal(
        {
            CONF_SERIAL_NUMBER: "1810088",
            CONF_TOKEN: "75868dcf8ea4c64e2063f6c4e70132d2",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def duplicate_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    sanix: MagicMock = Depends(mock_sanix),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that errors are shown when duplicates are added."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        CONFIG,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
