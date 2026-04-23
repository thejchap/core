"""Tests for the Meteo-France config flow."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.meteo_france.const import CONF_CITY, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    CITY_1,
    CITY_1_LAT,
    CITY_1_LON,
    CITY_1_POSTAL,
    CITY_2_NAME,
    CITY_3,
    CITY_3_LAT,
    CITY_3_LON,
    client_empty,
    client_multiple,
    client_single,
    mock_setup,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _ms: None = Depends(mock_setup),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def user(
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client_single),
) -> None:
    """Test user config."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_CITY: CITY_1_POSTAL},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal(f"{CITY_1_LAT}, {CITY_1_LON}")
    expect(result["title"]).to_equal(f"{CITY_1}")
    expect(result["data"][CONF_LATITUDE]).to_equal(str(CITY_1_LAT))
    expect(result["data"][CONF_LONGITUDE]).to_equal(str(CITY_1_LON))


@test
async def user_list(
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client_multiple),
) -> None:
    """Test user config with multiple city results."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_CITY: CITY_2_NAME},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("cities")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CITY: f"{CITY_3};{CITY_3_LAT};{CITY_3_LON}"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal(f"{CITY_3_LAT}, {CITY_3_LON}")
    expect(result["title"]).to_equal(f"{CITY_3}")
    expect(result["data"][CONF_LATITUDE]).to_equal(str(CITY_3_LAT))
    expect(result["data"][CONF_LONGITUDE]).to_equal(str(CITY_3_LON))


@test
async def search_failed(
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client_empty),
) -> None:
    """Test error displayed if no result in search."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_CITY: CITY_1_POSTAL},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({CONF_CITY: "empty"})


@test
async def abort_if_already_setup(
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client_single),
) -> None:
    """Test we abort if already setup."""
    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_LATITUDE: CITY_1_LAT, CONF_LONGITUDE: CITY_1_LON},
        unique_id=f"{CITY_1_LAT}, {CITY_1_LON}",
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_CITY: CITY_1_POSTAL},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
