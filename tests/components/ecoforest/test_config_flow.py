"""Tryke ports of the Ecoforest config flow tests."""

from unittest.mock import AsyncMock, Mock, patch

from pyecoforest.exceptions import EcoforestAuthenticationRequired
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.ecoforest.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    config,
    config_entry,
    mock_device,
    mock_setup_entry,
    serial_number,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Module-local fixture-resolution anchor."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    device: Mock = Depends(mock_device),
    cfg: dict = Depends(config),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch("pyecoforest.api.EcoforestApi.get", return_value=device):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], cfg
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
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
    expect(len(setup.mock_calls)).to_equal(1)


@test
async def form_device_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    entry: MockConfigEntry = Depends(config_entry),
    device: Mock = Depends(mock_device),
    cfg: dict = Depends(config),
) -> None:
    """Test device already exists."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch("pyecoforest.api.EcoforestApi.get", return_value=device):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], cfg
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "auth_required",
        error=EcoforestAuthenticationRequired("401"),
        message="invalid_auth",
    ),
    test.case(
        "cannot_connect",
        error=Exception("Something wrong"),
        message="cannot_connect",
    ),
)
async def flow_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    device: Mock = Depends(mock_device),
    cfg: dict = Depends(config),
    *,
    error: Exception,
    message: str,
) -> None:
    """Test we handle failed flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("pyecoforest.api.EcoforestApi.get", side_effect=error):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], cfg
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": message})

    with patch("pyecoforest.api.EcoforestApi.get", return_value=device):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], cfg
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
