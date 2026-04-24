"""Test the SensorPush Cloud config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from sensorpush_ha import SensorPushCloudAuthError
from tryke import Depends, expect, fixture, test

from homeassistant.components.sensorpush_cloud.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_api, mock_config_entry, mock_helper, mock_setup_entry
from .const import CONF_DATA, CONF_EMAIL

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_api),
    helper: AsyncMock = Depends(mock_helper),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user initialized flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        CONF_DATA,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test@example.com")
    expect(result["data"]).to_equal(CONF_DATA)
    expect(result["result"].unique_id).to_equal(CONF_DATA[CONF_EMAIL])
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def user_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_api),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we fail on a duplicate entry in the user flow."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONF_DATA
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("invalid_auth", error=SensorPushCloudAuthError, expected="invalid_auth"),
    test.case("unknown", error=Exception, expected="unknown"),
)
async def user_error(
    error: type[Exception],
    expected: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_api),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we display errors in the user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    api.async_authorize.side_effect = error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONF_DATA
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": expected})

    api.async_authorize.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONF_DATA
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test@example.com")
    expect(result["data"]).to_equal(CONF_DATA)
    expect(len(setup_entry.mock_calls)).to_equal(1)
