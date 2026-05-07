"""Tests for JVC Projector config flow."""

from unittest.mock import AsyncMock

from jvcprojector import JvcProjectorAuthError, JvcProjectorTimeoutError
from tryke import Depends, expect, fixture, test

from homeassistant.components.jvc_projector.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import MOCK_HOST, MOCK_PASSWORD, MOCK_PORT
from ._fixtures import (
    mock_config_entry,
    mock_device,
    mock_integration,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_config_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device: AsyncMock = Depends(mock_device),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user config flow success."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: MOCK_HOST,
            CONF_PORT: MOCK_PORT,
            CONF_PASSWORD: MOCK_PASSWORD,
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect("data" in result).to_be(True)
    expect(result["data"][CONF_HOST]).to_equal(MOCK_HOST)
    expect(result["data"][CONF_PORT]).to_equal(MOCK_PORT)
    expect(result["data"][CONF_PASSWORD]).to_equal(MOCK_PASSWORD)


@test
async def user_config_flow_bad_connect_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device: AsyncMock = Depends(mock_device),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test errors when connection error occurs."""
    mock_device.connect.side_effect = JvcProjectorTimeoutError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT, CONF_PASSWORD: MOCK_PASSWORD},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    # Finish flow with success

    mock_device.connect.side_effect = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT, CONF_PASSWORD: MOCK_PASSWORD},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect("data" in result).to_be(True)
    expect(result["data"][CONF_HOST]).to_equal(MOCK_HOST)
    expect(result["data"][CONF_PORT]).to_equal(MOCK_PORT)
    expect(result["data"][CONF_PASSWORD]).to_equal(MOCK_PASSWORD)


@test
async def user_config_flow_device_exists_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device: AsyncMock = Depends(mock_device),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_integration: MockConfigEntry = Depends(mock_integration),
) -> None:
    """Test flow aborts when device already configured."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT, CONF_PASSWORD: MOCK_PASSWORD},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_config_flow_bad_host_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device: AsyncMock = Depends(mock_device),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test errors when bad host error occurs."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "", CONF_PORT: MOCK_PORT, CONF_PASSWORD: MOCK_PASSWORD},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_host"})

    # Finish flow with success

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT, CONF_PASSWORD: MOCK_PASSWORD},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect("data" in result).to_be(True)
    expect(result["data"][CONF_HOST]).to_equal(MOCK_HOST)
    expect(result["data"][CONF_PORT]).to_equal(MOCK_PORT)
    expect(result["data"][CONF_PASSWORD]).to_equal(MOCK_PASSWORD)


@test
async def user_config_flow_bad_auth_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device: AsyncMock = Depends(mock_device),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test errors when bad auth error occurs."""
    mock_device.connect.side_effect = JvcProjectorAuthError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT, CONF_PASSWORD: MOCK_PASSWORD},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    # Finish flow with success

    mock_device.connect.side_effect = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT, CONF_PASSWORD: MOCK_PASSWORD},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect("data" in result).to_be(True)
    expect(result["data"][CONF_HOST]).to_equal(MOCK_HOST)
    expect(result["data"][CONF_PORT]).to_equal(MOCK_PORT)
    expect(result["data"][CONF_PASSWORD]).to_equal(MOCK_PASSWORD)


@test
async def reauth_config_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device: AsyncMock = Depends(mock_device),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_integration: MockConfigEntry = Depends(mock_integration),
) -> None:
    """Test reauth config flow success."""
    result = await mock_integration.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: MOCK_PASSWORD}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(mock_integration.data[CONF_HOST]).to_equal(MOCK_HOST)
    expect(mock_integration.data[CONF_PORT]).to_equal(MOCK_PORT)
    expect(mock_integration.data[CONF_PASSWORD]).to_equal(MOCK_PASSWORD)


@test
async def reauth_config_flow_auth_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device: AsyncMock = Depends(mock_device),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_integration: MockConfigEntry = Depends(mock_integration),
) -> None:
    """Test reauth config flow when connect fails."""
    mock_device.connect.side_effect = JvcProjectorAuthError

    result = await mock_integration.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: MOCK_PASSWORD}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    # Finish flow with success

    mock_device.connect.side_effect = None

    result = await mock_integration.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: MOCK_PASSWORD}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(mock_integration.data[CONF_HOST]).to_equal(MOCK_HOST)
    expect(mock_integration.data[CONF_PORT]).to_equal(MOCK_PORT)
    expect(mock_integration.data[CONF_PASSWORD]).to_equal(MOCK_PASSWORD)


@test
async def reauth_config_flow_connect_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device: AsyncMock = Depends(mock_device),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_integration: MockConfigEntry = Depends(mock_integration),
) -> None:
    """Test reauth config flow when connect fails."""
    mock_device.connect.side_effect = JvcProjectorTimeoutError

    result = await mock_integration.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: MOCK_PASSWORD}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    # Finish flow with success

    mock_device.connect.side_effect = None

    result = await mock_integration.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: MOCK_PASSWORD}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(mock_integration.data[CONF_HOST]).to_equal(MOCK_HOST)
    expect(mock_integration.data[CONF_PORT]).to_equal(MOCK_PORT)
    expect(mock_integration.data[CONF_PASSWORD]).to_equal(MOCK_PASSWORD)
