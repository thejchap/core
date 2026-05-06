"""Define tests for the AEMET OpenData config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from aemet_opendata.exceptions import AuthError
from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.components.aemet.const import (
    CONF_RADAR_UPDATES,
    CONF_STATION_UPDATES,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry
from .util import mock_api_call

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)

CONFIG = {
    CONF_NAME: "aemet",
    CONF_API_KEY: "foo",
    CONF_LATITUDE: 40.30403754,
    CONF_LONGITUDE: -3.72935236,
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the form is served with valid input."""
    with patch(
        "homeassistant.components.aemet.AEMET.api_call",
        side_effect=mock_api_call,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], CONFIG
        )

        await hass.async_block_till_done()

        conf_entries = hass.config_entries.async_entries(DOMAIN)
        entry = conf_entries[0]
        expect(entry.state).to_be(ConfigEntryState.LOADED)

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(CONFIG[CONF_NAME])
        expect(result["data"][CONF_LATITUDE]).to_equal(CONFIG[CONF_LATITUDE])
        expect(result["data"][CONF_LONGITUDE]).to_equal(CONFIG[CONF_LONGITUDE])
        expect(result["data"][CONF_API_KEY]).to_equal(CONFIG[CONF_API_KEY])

        expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "default",
        user_input={},
        expected={CONF_RADAR_UPDATES: False, CONF_STATION_UPDATES: True},
    ),
    test.case(
        "explicit_false",
        user_input={CONF_RADAR_UPDATES: False, CONF_STATION_UPDATES: False},
        expected={CONF_RADAR_UPDATES: False, CONF_STATION_UPDATES: False},
    ),
)
async def form_options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    *,
    user_input: dict[str, bool],
    expected: dict[str, bool],
) -> None:
    """Test the form options."""
    await hass.config.async_set_time_zone("UTC")
    freezer.move_to("2021-01-09 12:00:00+00:00")
    with patch(
        "homeassistant.components.aemet.AEMET.api_call",
        side_effect=mock_api_call,
    ):
        entry = MockConfigEntry(
            domain=DOMAIN, unique_id="40.30403754--3.72935236", data=CONFIG
        )
        entry.add_to_hass(hass)

        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        expect(entry.state).to_be(ConfigEntryState.LOADED)

        result = await hass.config_entries.options.async_init(entry.entry_id)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input=user_input
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(entry.options).to_equal(
            {
                CONF_RADAR_UPDATES: expected[CONF_RADAR_UPDATES],
                CONF_STATION_UPDATES: expected[CONF_STATION_UPDATES],
            }
        )

        await hass.async_block_till_done()

        expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def form_duplicated_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test setting up duplicated entry."""
    await hass.config.async_set_time_zone("UTC")
    freezer.move_to("2021-01-09 12:00:00+00:00")
    with patch(
        "homeassistant.components.aemet.AEMET.api_call",
        side_effect=mock_api_call,
    ):
        entry = MockConfigEntry(
            domain=DOMAIN, unique_id="40.30403754--3.72935236", data=CONFIG
        )
        entry.add_to_hass(hass)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")


@test
async def form_auth_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up with api auth error."""
    mocked_aemet = MagicMock()
    mocked_aemet.select_coordinates.side_effect = AuthError

    with patch(
        "homeassistant.components.aemet.config_flow.AEMET",
        return_value=mocked_aemet,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
        )

        expect(result["errors"]).to_equal({"base": "invalid_api_key"})
