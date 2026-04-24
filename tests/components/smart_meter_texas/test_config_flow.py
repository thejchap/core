"""Test the Smart Meter Texas config flow."""

from __future__ import annotations

from unittest.mock import patch

from aiohttp import ClientError
from smart_meter_texas.exceptions import (
    SmartMeterTexasAPIError,
    SmartMeterTexasAuthError,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.smart_meter_texas.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_LOGIN = {CONF_USERNAME: "test-username", CONF_PASSWORD: "test-password"}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch("smart_meter_texas.Client.authenticate", return_value=True),
        patch(
            "homeassistant.components.smart_meter_texas.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_LOGIN
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(TEST_LOGIN[CONF_USERNAME])
    expect(result2["data"]).to_equal(TEST_LOGIN)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "smart_meter_texas.Client.authenticate",
        side_effect=SmartMeterTexasAuthError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_LOGIN,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test.cases(
    test.case("timeout", side_effect=TimeoutError),
    test.case("client_error", side_effect=ClientError),
    test.case("api_error", side_effect=SmartMeterTexasAPIError),
)
async def form_cannot_connect(
    side_effect: type[Exception],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "smart_meter_texas.Client.authenticate",
        side_effect=side_effect,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_LOGIN
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unknown_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test base exception is handled."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "smart_meter_texas.Client.authenticate",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_LOGIN,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def form_duplicate_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that a duplicate account cannot be configured."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="user123",
        data={"username": "user123", "password": "password123"},
    ).add_to_hass(hass)

    with patch(
        "smart_meter_texas.Client.authenticate",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"username": "user123", "password": "password123"},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
