"""Test the Chess.com config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from chess_com_api import NotFoundError
from tryke import Depends, expect, fixture, test

from homeassistant.components.chess_com.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.chess_com._fixtures import (
    mock_chess_client,
    mock_config_entry,
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
    _mock_chess_client: AsyncMock = Depends(mock_chess_client),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "joostlek"}
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("Joost")
    expect(result["data"]).to_equal({CONF_USERNAME: "joostlek"})
    expect(result["result"].unique_id).to_equal("532748851")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def flow_no_name(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_chess_client: AsyncMock = Depends(mock_chess_client),
) -> None:
    """Test the flow with no name."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    mock_chess_client.get_player.return_value.name = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "joostlek"}
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("joostlek")
    expect(result["data"]).to_equal({CONF_USERNAME: "joostlek"})
    expect(result["result"].unique_id).to_equal("532748851")


@test.cases(
    test.case("player_not_found", NotFoundError, "player_not_found"),
    test.case("unknown", Exception, "unknown"),
)
async def form_errors(
    exception: Exception,
    error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_chess_client: AsyncMock = Depends(mock_chess_client),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle form errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    mock_chess_client.get_player.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "joostlek"}
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": error})

    mock_chess_client.get_player.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "joostlek"}
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def duplicate_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_chess_client: AsyncMock = Depends(mock_chess_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we handle duplicate entries."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "joostlek"}
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")
