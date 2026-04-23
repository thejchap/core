"""Test the Dexcom config flow."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pydexcom.errors import AccountError, SessionError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.dexcom.const import DOMAIN
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.dexcom import CONFIG
from tests.components.dexcom._fixtures import mock_zeroconf
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    with (
        patch("homeassistant.components.dexcom.config_flow.Dexcom"),
        patch(
            "homeassistant.components.dexcom.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal(CONFIG[CONF_USERNAME])
    expect(result2["data"]).to_equal(CONFIG)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_account_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we handle account error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.dexcom.config_flow.Dexcom",
        side_effect=AccountError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_session_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we handle session error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.dexcom.config_flow.Dexcom",
        side_effect=SessionError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unknown_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.dexcom.config_flow.Dexcom",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": "unknown"})
