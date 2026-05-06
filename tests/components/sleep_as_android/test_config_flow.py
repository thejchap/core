"""Test the Sleep as Android config flow."""

from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.sleep_as_android.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network


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
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    with (
        patch(
            "homeassistant.components.webhook.async_generate_id",
            return_value="webhook_id",
        ),
        patch(
            "homeassistant.components.webhook.async_generate_url",
            return_value="http://example.com:8123",
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Sleep as Android")
    expect(result["data"]).to_equal(
        {
            "cloudhook": False,
            CONF_WEBHOOK_ID: "webhook_id",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)
