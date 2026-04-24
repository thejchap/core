"""Define tests for the 17Track config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from pyseventeentrack.errors import SeventeenTrackError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.seventeentrack import DOMAIN
from homeassistant.components.seventeentrack.const import (
    CONF_SHOW_ARCHIVED,
    CONF_SHOW_DELIVERED,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry, mock_seventeentrack

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

VALID_CONFIG = {
    CONF_USERNAME: "someemail@gmail.com",
    CONF_PASSWORD: "edc3eee7330e4fdda04489e3fbc283d0",
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    seventeentrack: AsyncMock = Depends(mock_seventeentrack),
) -> None:
    """Test that the user step works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        VALID_CONFIG,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("someemail@gmail.com")
    expect(result2["data"]).to_equal(
        {
            CONF_PASSWORD: "edc3eee7330e4fdda04489e3fbc283d0",
            CONF_USERNAME: "someemail@gmail.com",
        }
    )


@test.cases(
    test.case("invalid_auth", return_value=False, side_effect=None, error="invalid_auth"),
    test.case(
        "cannot_connect",
        return_value=True,
        side_effect=SeventeenTrackError(),
        error="cannot_connect",
    ),
)
async def flow_fails(
    return_value: bool,
    side_effect: Exception | None,
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    seventeentrack: AsyncMock = Depends(mock_seventeentrack),
) -> None:
    """Test that the user step fails."""
    seventeentrack.return_value.profile.login.return_value = return_value
    seventeentrack.return_value.profile.login.side_effect = side_effect
    failed_result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=VALID_CONFIG,
    )

    expect(failed_result["errors"]).to_equal({"base": error})

    seventeentrack.return_value.profile.login.return_value = True
    seventeentrack.return_value.profile.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        failed_result["flow_id"],
        VALID_CONFIG,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("someemail@gmail.com")
    expect(result["data"]).to_equal(
        {
            CONF_PASSWORD: "edc3eee7330e4fdda04489e3fbc283d0",
            CONF_USERNAME: "someemail@gmail.com",
        }
    )


@test
async def option_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    seventeentrack: AsyncMock = Depends(mock_seventeentrack),
) -> None:
    """Test option flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_CONFIG,
        options={
            CONF_SHOW_ARCHIVED: False,
            CONF_SHOW_DELIVERED: False,
        },
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_SHOW_ARCHIVED: True, CONF_SHOW_DELIVERED: False},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_SHOW_ARCHIVED]).to_be(True)
    expect(result["data"][CONF_SHOW_DELIVERED]).to_be(False)
