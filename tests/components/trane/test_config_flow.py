"""Tests for the Trane Local config flow."""

from unittest.mock import AsyncMock, MagicMock

from steamloop import PairingError, SteamloopConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.trane.const import CONF_SECRET_KEY, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    MOCK_HOST,
    MOCK_SECRET_KEY,
    mock_config_entry,
    mock_connection,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _connection: MagicMock = Depends(mock_connection),
) -> None:
    """Test the full user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: MOCK_HOST},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"Thermostat ({MOCK_HOST})")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: MOCK_HOST,
            CONF_SECRET_KEY: MOCK_SECRET_KEY,
        }
    )
    expect(result["result"].unique_id).to_be(None)


@test.cases(
    test.case(
        "connection_error",
        side_effect=SteamloopConnectionError,
        error_key="cannot_connect",
    ),
    test.case(
        "pairing_error",
        side_effect=PairingError,
        error_key="cannot_connect",
    ),
    test.case(
        "runtime_error",
        side_effect=RuntimeError,
        error_key="unknown",
    ),
)
async def form_errors_can_recover(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    connection: MagicMock = Depends(mock_connection),
    *,
    side_effect: type[Exception],
    error_key: str,
) -> None:
    """Test errors and recovery during config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    connection.pair.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: MOCK_HOST},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_key})

    connection.pair.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: MOCK_HOST},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"Thermostat ({MOCK_HOST})")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: MOCK_HOST,
            CONF_SECRET_KEY: MOCK_SECRET_KEY,
        }
    )


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _connection: MagicMock = Depends(mock_connection),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test config flow aborts when already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: MOCK_HOST},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
