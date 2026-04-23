"""Test the Ecoforest config flow."""

from unittest.mock import AsyncMock, Mock, patch

from pyecoforest.exceptions import EcoforestAuthenticationRequired
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.ecoforest.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.ecoforest._fixtures import (
    config,
    config_entry,
    mock_device,
    mock_setup_entry,
    serial_number,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_device: Mock = Depends(mock_device),
    config: dict[str, str] = Depends(config),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    with patch(
        "pyecoforest.api.EcoforestApi.get",
        return_value=mock_device,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            config,
        )
        await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect("result" in result).to_be(True)
    expect(result["result"].unique_id).to_equal("1234")
    expect(result["title"]).to_equal("Ecoforest 1234")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "1.1.1.1",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_device_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _config_entry: MockConfigEntry = Depends(config_entry),
    mock_device: Mock = Depends(mock_device),
    config: dict[str, str] = Depends(config),
) -> None:
    """Test device already exists."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    with patch(
        "pyecoforest.api.EcoforestApi.get",
        return_value=mock_device,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            config,
        )
        await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "auth_required",
        EcoforestAuthenticationRequired("401"),
        "invalid_auth",
    ),
    test.case(
        "unknown_exception",
        Exception("Something wrong"),
        "cannot_connect",
    ),
)
async def flow_fails(
    error: Exception,
    message: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_device: Mock = Depends(mock_device),
    config: dict[str, str] = Depends(config),
) -> None:
    """Test we handle failed flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "pyecoforest.api.EcoforestApi.get",
        side_effect=error,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            config,
        )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": message})

    with patch(
        "pyecoforest.api.EcoforestApi.get",
        return_value=mock_device,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            config,
        )
        await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
