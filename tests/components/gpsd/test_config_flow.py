"""Test the GPSD config flow."""

from unittest.mock import AsyncMock, patch

from gps3.agps3threaded import GPSD_PORT as DEFAULT_PORT
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.gpsd.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network

HOST = "gpsd.local"


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    with patch("socket.socket") as mock_socket:
        mock_connect = mock_socket.return_value.connect
        mock_connect.return_value = None

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: HOST,
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(f"GPS {HOST}")
    expect(result2["data"]).to_equal(
        {
            CONF_HOST: HOST,
            CONF_PORT: DEFAULT_PORT,
        }
    )
    setup_entry.assert_called_once()


@test
async def connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test connection to host error."""
    with patch("socket.socket", side_effect=OSError):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_HOST: "nonexistent.local", CONF_PORT: 1234},
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("cannot_connect")
