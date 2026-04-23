"""Test the APsystems Local API config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.apsystems.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.apsystems._fixtures import (
    mock_apsystems,
    mock_config_entry,
    mock_setup_entry,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form_create_success(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_apsystems: AsyncMock = Depends(mock_apsystems),
) -> None:
    """Test we handle creating with success."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_IP_ADDRESS: "127.0.0.1",
        },
    )
    expect(result["result"].unique_id).to_equal("MY_SERIAL_NUMBER")
    expect(result.get("type") is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["data"].get(CONF_IP_ADDRESS)).to_equal("127.0.0.1")


@test
async def form_create_success_custom_port(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_apsystems: AsyncMock = Depends(mock_apsystems),
) -> None:
    """Test we handle creating with custom port with success."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_IP_ADDRESS: "127.0.0.1",
            CONF_PORT: 8042,
        },
    )
    expect(result["result"].unique_id).to_equal("MY_SERIAL_NUMBER")
    expect(result.get("type") is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["data"].get(CONF_IP_ADDRESS)).to_equal("127.0.0.1")
    expect(result["data"].get(CONF_PORT)).to_equal(8042)


@test
async def form_cannot_connect_and_recover(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_apsystems: AsyncMock = Depends(mock_apsystems),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle cannot connect error."""

    mock_apsystems.get_device_info.side_effect = TimeoutError
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_IP_ADDRESS: "127.0.0.2",
        },
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    mock_apsystems.get_device_info.side_effect = None

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_IP_ADDRESS: "127.0.0.1",
        },
    )
    expect(result2["result"].unique_id).to_equal("MY_SERIAL_NUMBER")
    expect(result2.get("type") is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["data"].get(CONF_IP_ADDRESS)).to_equal("127.0.0.1")


@test
async def form_cannot_connect_and_recover_custom_port(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_apsystems: AsyncMock = Depends(mock_apsystems),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle cannot connect error but recovering with custom port."""

    mock_apsystems.get_device_info.side_effect = TimeoutError
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_IP_ADDRESS: "127.0.0.2", CONF_PORT: 8042},
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    mock_apsystems.get_device_info.side_effect = None

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_IP_ADDRESS: "127.0.0.1", CONF_PORT: 8042},
    )
    expect(result2["result"].unique_id).to_equal("MY_SERIAL_NUMBER")
    expect(result2.get("type") is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["data"].get(CONF_IP_ADDRESS)).to_equal("127.0.0.1")
    expect(result2["data"].get(CONF_PORT)).to_equal(8042)


@test
async def form_unique_id_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_apsystems: AsyncMock = Depends(mock_apsystems),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we handle cannot connect error."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_IP_ADDRESS: "127.0.0.2",
        },
    )
    expect(result["reason"]).to_equal("already_configured")
    expect(result.get("type") is FlowResultType.ABORT).to_be(True)
