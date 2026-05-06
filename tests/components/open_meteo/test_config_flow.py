"""Tests for the Open-Meteo config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.open_meteo.const import DOMAIN
from homeassistant.components.zone import ENTITY_ID_HOME
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_ZONE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor(
    _setup: None = Depends(mock_setup_entry),
) -> None:
    """Module-level fixture that primes mock_setup_entry."""


@test
async def full_user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ZONE: ENTITY_ID_HOME},
    )

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("title")).to_equal("test home")
    expect(result2.get("data")).to_equal({CONF_ZONE: ENTITY_ID_HOME})
