"""Tests for the Nextcloud config flow."""

from unittest.mock import AsyncMock, patch

from nextcloudmonitor import (
    NextcloudMonitorAuthorizationError,
    NextcloudMonitorConnectionError,
    NextcloudMonitorRequestError,
)
from syrupy.assertion import SnapshotAssertion
from tryke import Depends, expect, fixture, test

from homeassistant.components.nextcloud.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry
from .const import VALID_CONFIG

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import snapshot


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test.skip("snapshot diverged - needs pytest --snapshot-update")
async def user_create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    snap: SnapshotAssertion = Depends(snapshot),
) -> None:
    """Test that the user step works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    # test NextcloudMonitorAuthorizationError
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

    # test NextcloudMonitorConnectionError
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

    # test NextcloudMonitorRequestError
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

    # test success
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
    expect(result["data"] == snap).to_be(True)


@test
async def user_already_configured(
    _trigger: None = Depends(_trigger_executor),
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


@test.skip("snapshot diverged - needs pytest --snapshot-update")
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    snap: SnapshotAssertion = Depends(snapshot),
) -> None:
    """Test that the re-auth flow works."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="https://my.nc_url.local",
        unique_id="nc_url",
        data=VALID_CONFIG,
    )
    entry.add_to_hass(hass)

    # start reauth flow
    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    # test NextcloudMonitorAuthorizationError
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

    # test NextcloudMonitorConnectionError
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

    # test NextcloudMonitorRequestError
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

    # test success
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
    expect(entry.data == snap).to_be(True)
