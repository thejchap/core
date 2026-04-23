"""Test AfterShip config flow."""

from unittest.mock import AsyncMock, patch

from pyaftership import AfterShipException
from tryke import Depends, expect, fixture, test

from homeassistant.components.aftership.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.aftership._fixtures import mock_setup_entry
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def full_user_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    with patch(
        "homeassistant.components.aftership.config_flow.AfterShip",
        return_value=AsyncMock(),
    ) as mock_aftership:
        mock_aftership.return_value.trackings.return_value.list.return_value = {}
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_API_KEY: "mock-api-key"},
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("AfterShip")
        expect(result["data"]).to_equal({CONF_API_KEY: "mock-api-key"})


@test
async def flow_cannot_connect(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test handling invalid connection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    with patch(
        "homeassistant.components.aftership.config_flow.AfterShip",
        return_value=AsyncMock(),
    ) as mock_aftership:
        mock_aftership.side_effect = AfterShipException
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_API_KEY: "mock-api-key"},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.aftership.config_flow.AfterShip",
        return_value=AsyncMock(),
    ) as mock_aftership:
        mock_aftership.return_value.trackings.return_value.list.return_value = {}
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_API_KEY: "mock-api-key"},
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("AfterShip")
        expect(result["data"]).to_equal({CONF_API_KEY: "mock-api-key"})
