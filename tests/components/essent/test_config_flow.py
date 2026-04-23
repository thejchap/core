"""Tests for Essent config flow."""

from unittest.mock import AsyncMock, MagicMock

from essent_dynamic_pricing import (
    EssentConnectionError,
    EssentDataError,
    EssentResponseError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.essent.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.essent._fixtures import (
    mock_config_entry,
    mock_essent_client,
    mock_setup_entry,
    mock_zeroconf,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_essent_client: AsyncMock = Depends(mock_essent_client),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test successful config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("Essent")
    expect(result["data"]).to_equal({})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test abort when already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test.cases(
    test.case("connection_error", EssentConnectionError, "cannot_connect"),
    test.case("response_error", EssentResponseError("bad"), "cannot_connect"),
    test.case("data_error", EssentDataError("bad"), "invalid_data"),
    test.case("unknown", Exception, "unknown"),
)
async def flow_errors(
    exception: Exception,
    error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_essent_client: AsyncMock = Depends(mock_essent_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test flow errors."""
    mock_essent_client.async_get_prices.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal(error)
