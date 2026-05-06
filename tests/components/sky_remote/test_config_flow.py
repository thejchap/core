"""Test the Sky Remote config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from skyboxremote import LEGACY_PORT, SkyBoxConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.sky_remote.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    SAMPLE_CONFIG,
    mock_config_entry,
    mock_remote_control,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    remote_control: MagicMock = Depends(mock_remote_control),
) -> None:
    """Test we can setup an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: SAMPLE_CONFIG[CONF_HOST]},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(SAMPLE_CONFIG)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def device_exists_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    remote_control: MagicMock = Depends(mock_remote_control),
) -> None:
    """Test we abort flow if device already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: config_entry.data[CONF_HOST]},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_flow_legacy_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    remote_control: MagicMock = Depends(mock_remote_control),
) -> None:
    """Test we can setup an entry with a legacy port."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)

    async def mock_check_connectable() -> bool:
        if remote_control.call_args[0][1] == LEGACY_PORT:
            return True
        raise SkyBoxConnectionError("Wrong port")

    remote_control._instance_mock.check_connectable = mock_check_connectable

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: SAMPLE_CONFIG[CONF_HOST]},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({**SAMPLE_CONFIG, CONF_PORT: LEGACY_PORT})
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def user_flow_unconnectable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    remote_control: MagicMock = Depends(mock_remote_control),
) -> None:
    """Test we can setup an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)

    remote_control._instance_mock.check_connectable = AsyncMock(
        side_effect=SkyBoxConnectionError("Example")
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: SAMPLE_CONFIG[CONF_HOST]},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})
    expect(len(setup_entry.mock_calls)).to_equal(0)

    remote_control._instance_mock.check_connectable = AsyncMock(True)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: SAMPLE_CONFIG[CONF_HOST]},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(SAMPLE_CONFIG)
    expect(len(setup_entry.mock_calls)).to_equal(1)
