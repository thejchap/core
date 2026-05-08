"""Tryke fixtures for the kodi integration."""

from tryke import Depends, fixture

from homeassistant import config_entries
from homeassistant.components.kodi.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def user_flow_id(
    hass: HomeAssistant = Depends(hass_fixture),
) -> str:
    """Return a user-initiated flow after filling in host info."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    return result["flow_id"]
