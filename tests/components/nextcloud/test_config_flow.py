"""Tests for the Nextcloud config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from nextcloudmonitor import (
    NextcloudMonitorAuthorizationError,
    NextcloudMonitorConnectionError,
    NextcloudMonitorRequestError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.nextcloud.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.nextcloud._fixtures import mock_setup_entry
from tests.components.nextcloud.const import VALID_CONFIG
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Wire mocks for every test."""


@test
async def user_create_entry(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that the user step works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.nextcloud.config_flow.NextcloudMonitor",
        side_effect=NextcloudMonitorAuthorizationError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    with patch(
        "homeassistant.components.nextcloud.config_flow.NextcloudMonitor",
        side_effect=NextcloudMonitorConnectionError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "connection_error"})

    with patch(
        "homeassistant.components.nextcloud.config_flow.NextcloudMonitor",
        side_effect=NextcloudMonitorRequestError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "connection_error"})

    with patch(
        "homeassistant.components.nextcloud.config_flow.NextcloudMonitor",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("https://my.nc_url.local")
    expect(result["data"]).to_equal(
        {
            "password": "nc_pass",
            "url": "https://my.nc_url.local",
            "username": "nc_user",
            "verify_ssl": True,
        }
    )


@test
async def user_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that errors are shown when duplicates are added."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="https://my.nc_url.local",
        unique_id="nc_url",
        data=VALID_CONFIG,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.nextcloud.config_flow.NextcloudMonitor",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that the re-auth flow works."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="https://my.nc_url.local",
        unique_id="nc_url",
        data=VALID_CONFIG,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.nextcloud.config_flow.NextcloudMonitor",
        side_effect=NextcloudMonitorAuthorizationError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "other_user",
                CONF_PASSWORD: "other_password",
            },
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    with patch(
        "homeassistant.components.nextcloud.config_flow.NextcloudMonitor",
        side_effect=NextcloudMonitorConnectionError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "other_user",
                CONF_PASSWORD: "other_password",
            },
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": "connection_error"})

    with patch(
        "homeassistant.components.nextcloud.config_flow.NextcloudMonitor",
        side_effect=NextcloudMonitorRequestError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "other_user",
                CONF_PASSWORD: "other_password",
            },
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": "connection_error"})

    with patch(
        "homeassistant.components.nextcloud.config_flow.NextcloudMonitor",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "other_user",
                CONF_PASSWORD: "other_password",
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(dict(entry.data)).to_equal(
        {
            "password": "other_password",
            "url": "https://my.nc_url.local",
            "username": "other_user",
            "verify_ssl": True,
        }
    )
