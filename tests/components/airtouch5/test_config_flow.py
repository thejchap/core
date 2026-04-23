"""Test the Airtouch 5 config flow."""

from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.airtouch5.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.airtouch5._fixtures import mock_setup_entry
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def success(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"] is None).to_be(True)

    host = "1.1.1.1"

    with patch(
        "airtouch5py.airtouch5_simple_client.Airtouch5SimpleClient.test_connection",
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": host},
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal(host)
    expect(result2["data"]).to_equal({"host": host})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def cannot_connect(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "airtouch5py.airtouch5_simple_client.Airtouch5SimpleClient.test_connection",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1"},
        )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})
