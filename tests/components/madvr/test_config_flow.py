"""Tests for the MadVR config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.madvr.const import DEFAULT_NAME, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    avoid_wait,
    mock_config_entry,
    mock_madvr_client,
    mock_setup_entry,
)
from .const import MOCK_CONFIG, MOCK_MAC, MOCK_MAC_NEW

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _aw: None = Depends(avoid_wait),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_madvr_client: AsyncMock = Depends(mock_madvr_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test full config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: MOCK_CONFIG[CONF_HOST], CONF_PORT: MOCK_CONFIG[CONF_PORT]},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: MOCK_CONFIG[CONF_HOST],
            CONF_PORT: MOCK_CONFIG[CONF_PORT],
        }
    )
    expect(result["result"].unique_id).to_equal(MOCK_MAC)
    mock_madvr_client.open_connection.assert_called_once()
    mock_madvr_client.async_add_tasks.assert_called_once()
    mock_madvr_client.async_cancel_tasks.assert_called_once()


@test
async def flow_errors(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_madvr_client: AsyncMock = Depends(mock_madvr_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test error handling in config flow."""
    mock_madvr_client.open_connection.side_effect = TimeoutError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: MOCK_CONFIG[CONF_HOST], CONF_PORT: MOCK_CONFIG[CONF_PORT]},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    mock_madvr_client.open_connection.side_effect = None
    mock_madvr_client.connected = False
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: MOCK_CONFIG[CONF_HOST], CONF_PORT: MOCK_CONFIG[CONF_PORT]},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    mock_madvr_client.connected = True
    mock_madvr_client.mac_address = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: MOCK_CONFIG[CONF_HOST], CONF_PORT: MOCK_CONFIG[CONF_PORT]},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "no_mac"})

    mock_madvr_client.mac_address = MOCK_MAC
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: MOCK_CONFIG[CONF_HOST], CONF_PORT: MOCK_CONFIG[CONF_PORT]},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: MOCK_CONFIG[CONF_HOST],
            CONF_PORT: MOCK_CONFIG[CONF_PORT],
        }
    )

    expect(mock_madvr_client.open_connection.call_count).to_equal(4)
    expect(mock_madvr_client.async_add_tasks.call_count).to_equal(2)
    expect(mock_madvr_client.async_cancel_tasks.call_count).to_equal(2)


@test
async def duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_madvr_client: AsyncMock = Depends(mock_madvr_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate config entries."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: MOCK_CONFIG[CONF_HOST], CONF_PORT: MOCK_CONFIG[CONF_PORT]},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reconfigure_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_madvr_client: AsyncMock = Depends(mock_madvr_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({})

    new_host = "192.168.1.100"
    new_port = 44078

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: new_host, CONF_PORT: new_port},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    expect(mock_config_entry.data[CONF_HOST]).to_equal(new_host)
    expect(mock_config_entry.data[CONF_PORT]).to_equal(new_port)

    mock_madvr_client.open_connection.assert_called()
    mock_madvr_client.async_add_tasks.assert_called()
    mock_madvr_client.async_cancel_tasks.assert_called()


@test
async def reconfigure_new_device(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_madvr_client: AsyncMock = Depends(mock_madvr_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure with a new device (should fail)."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    new_host = "192.168.1.100"
    new_port = 44078

    mock_madvr_client.mac_address = MOCK_MAC_NEW
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: new_host, CONF_PORT: new_port},
    )

    expect(mock_config_entry.unique_id).to_equal(MOCK_MAC)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("set_up_new_device")


@test
async def reconfigure_flow_errors(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_madvr_client: AsyncMock = Depends(mock_madvr_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test error handling in reconfigure flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_madvr_client.open_connection.side_effect = TimeoutError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.100", CONF_PORT: 44077},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    mock_madvr_client.open_connection.side_effect = None
    mock_madvr_client.connected = True
    mock_madvr_client.mac_address = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.100", CONF_PORT: 44077},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "no_mac"})

    mock_madvr_client.mac_address = MOCK_MAC
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.100", CONF_PORT: 44077},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
