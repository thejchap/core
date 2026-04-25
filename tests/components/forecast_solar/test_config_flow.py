"""Test the Forecast.Solar config flow."""

from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.forecast_solar.const import (
    CONF_AZIMUTH,
    CONF_DAMPING_EVENING,
    CONF_DAMPING_MORNING,
    CONF_DECLINATION,
    CONF_INVERTER_SIZE,
    CONF_MODULES_POWER,
    DOMAIN,
    SUBENTRY_TYPE_PLANE,
)
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    SOURCE_USER,
    ConfigSubentryData,
)
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_forecast_solar, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Name",
            CONF_LATITUDE: 52.42,
            CONF_LONGITUDE: 4.42,
            CONF_AZIMUTH: 142,
            CONF_DECLINATION: 42,
            CONF_MODULES_POWER: 4242,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    config_entry = result["result"]
    expect(config_entry.title).to_equal("Name")
    expect(config_entry.unique_id).to_be(None)
    expect(dict(config_entry.data)).to_equal(
        {
            CONF_LATITUDE: 52.42,
            CONF_LONGITUDE: 4.42,
        }
    )
    expect(dict(config_entry.options)).to_equal({})

    plane_subentries = config_entry.get_subentries_of_type(SUBENTRY_TYPE_PLANE)
    expect(len(plane_subentries)).to_equal(1)
    subentry = plane_subentries[0]
    expect(subentry.subentry_type).to_equal(SUBENTRY_TYPE_PLANE)
    expect(dict(subentry.data)).to_equal(
        {
            CONF_DECLINATION: 42,
            CONF_AZIMUTH: 142,
            CONF_MODULES_POWER: 4242,
        }
    )
    expect(subentry.title).to_equal("42° / 142° / 4242W")

    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def options_flow_invalid_api(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test options config flow when API key is invalid."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "solarPOWER!",
            CONF_DAMPING_MORNING: 0.25,
            CONF_DAMPING_EVENING: 0.25,
            CONF_INVERTER_SIZE: 2000,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({CONF_API_KEY: "invalid_api_key"})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "SolarForecast150",
            CONF_DAMPING_MORNING: 0.25,
            CONF_DAMPING_EVENING: 0.25,
            CONF_INVERTER_SIZE: 2000,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(dict(result["data"])).to_equal(
        {
            CONF_API_KEY: "SolarForecast150",
            CONF_DAMPING_MORNING: 0.25,
            CONF_DAMPING_EVENING: 0.25,
            CONF_INVERTER_SIZE: 2000,
        }
    )


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test config flow options."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "SolarForecast150",
            CONF_DAMPING_MORNING: 0.25,
            CONF_DAMPING_EVENING: 0.25,
            CONF_INVERTER_SIZE: 2000,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(dict(result["data"])).to_equal(
        {
            CONF_API_KEY: "SolarForecast150",
            CONF_DAMPING_MORNING: 0.25,
            CONF_DAMPING_EVENING: 0.25,
            CONF_INVERTER_SIZE: 2000,
        }
    )


@test
async def options_flow_required_api_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test config flow options requires API key when multiple planes are present."""
    config_entry = MockConfigEntry(
        title="Green House",
        unique_id="unique",
        version=3,
        domain=DOMAIN,
        data={
            CONF_LATITUDE: 52.42,
            CONF_LONGITUDE: 4.42,
        },
        options={
            CONF_DAMPING_MORNING: 0.5,
            CONF_DAMPING_EVENING: 0.5,
            CONF_INVERTER_SIZE: 2000,
            CONF_API_KEY: "abcdef1234567890",
        },
        subentries_data=[
            ConfigSubentryData(
                data={
                    CONF_DECLINATION: 30,
                    CONF_AZIMUTH: 190,
                    CONF_MODULES_POWER: 5100,
                },
                subentry_id="mock_plane_id",
                subentry_type=SUBENTRY_TYPE_PLANE,
                title="30° / 190° / 5100W",
                unique_id=None,
            ),
            ConfigSubentryData(
                data={
                    CONF_DECLINATION: 45,
                    CONF_AZIMUTH: 270,
                    CONF_MODULES_POWER: 3000,
                },
                subentry_id="second_plane_id",
                subentry_type=SUBENTRY_TYPE_PLANE,
                title="45° / 270° / 3000W",
                unique_id=None,
            ),
        ],
    )

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "",
            CONF_DAMPING_MORNING: 0.25,
            CONF_DAMPING_EVENING: 0.25,
            CONF_INVERTER_SIZE: 2000,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({CONF_API_KEY: "api_key_required"})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "SolarForecast150",
            CONF_DAMPING_MORNING: 0.25,
            CONF_DAMPING_EVENING: 0.25,
            CONF_INVERTER_SIZE: 2000,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(dict(result["data"])).to_equal(
        {
            CONF_API_KEY: "SolarForecast150",
            CONF_DAMPING_MORNING: 0.25,
            CONF_DAMPING_EVENING: 0.25,
            CONF_INVERTER_SIZE: 2000,
        }
    )


@test
async def subentry_flow_add_plane(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test adding a plane via subentry flow."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, SUBENTRY_TYPE_PLANE),
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_DECLINATION: 45,
            CONF_AZIMUTH: 270,
            CONF_MODULES_POWER: 3000,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("45° / 270° / 3000W")
    expect(dict(result["data"])).to_equal(
        {
            CONF_DECLINATION: 45,
            CONF_AZIMUTH: 270,
            CONF_MODULES_POWER: 3000,
        }
    )

    expect(len(config_entry.get_subentries_of_type(SUBENTRY_TYPE_PLANE))).to_equal(2)


@test
async def subentry_flow_reconfigure_plane(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _solar: MagicMock = Depends(mock_forecast_solar),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguring a plane via subentry flow."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    subentry_id = config_entry.get_subentries_of_type(SUBENTRY_TYPE_PLANE)[
        0
    ].subentry_id

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, SUBENTRY_TYPE_PLANE),
        context={"source": SOURCE_RECONFIGURE, "subentry_id": subentry_id},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_DECLINATION: 50,
            CONF_AZIMUTH: 200,
            CONF_MODULES_POWER: 6000,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    plane_subentries = config_entry.get_subentries_of_type(SUBENTRY_TYPE_PLANE)
    expect(len(plane_subentries)).to_equal(1)
    subentry = plane_subentries[0]
    expect(dict(subentry.data)).to_equal(
        {
            CONF_DECLINATION: 50,
            CONF_AZIMUTH: 200,
            CONF_MODULES_POWER: 6000,
        }
    )
    expect(subentry.title).to_equal("50° / 200° / 6000W")


@test.skip("requires api_key_present=False parametrize override")
async def subentry_flow_no_api_key() -> None:
    """Test that adding more than one plane without API key is not allowed."""


@test
async def subentry_flow_max_planes(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that adding more than 4 planes is not allowed."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    for i in range(3):
        result = await hass.config_entries.subentries.async_init(
            (config_entry.entry_id, SUBENTRY_TYPE_PLANE),
            context={"source": SOURCE_USER},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            user_input={
                CONF_DECLINATION: 10 * (i + 1),
                CONF_AZIMUTH: 90 * (i + 1),
                CONF_MODULES_POWER: 1000 * (i + 1),
            },
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    expect(len(config_entry.get_subentries_of_type(SUBENTRY_TYPE_PLANE))).to_equal(4)

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, SUBENTRY_TYPE_PLANE),
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("max_planes")


@test
async def subentry_flow_reconfigure_plane_not_loaded(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguring a plane via subentry flow when entry is not loaded."""
    config_entry.add_to_hass(hass)

    subentry_id = config_entry.get_subentries_of_type(SUBENTRY_TYPE_PLANE)[
        0
    ].subentry_id

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, SUBENTRY_TYPE_PLANE),
        context={"source": SOURCE_RECONFIGURE, "subentry_id": subentry_id},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_DECLINATION: 50,
            CONF_AZIMUTH: 200,
            CONF_MODULES_POWER: 6000,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    plane_subentries = config_entry.get_subentries_of_type(SUBENTRY_TYPE_PLANE)
    expect(len(plane_subentries)).to_equal(1)
    subentry = plane_subentries[0]
    expect(dict(subentry.data)).to_equal(
        {
            CONF_DECLINATION: 50,
            CONF_AZIMUTH: 200,
            CONF_MODULES_POWER: 6000,
        }
    )
    expect(subentry.title).to_equal("50° / 200° / 6000W")
