"""Test the Tomorrow.io config flow."""

from unittest.mock import patch

from pytomorrowio.exceptions import (
    CantConnectException,
    InvalidAPIKeyException,
    RateLimitedException,
    UnknownException,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.tomorrowio.config_flow import (
    _get_config_schema,
    _get_unique_id,
)
from homeassistant.components.tomorrowio.const import (
    CONF_TIMESTEP,
    DEFAULT_NAME,
    DEFAULT_TIMESTEP,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_RADIUS,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from ._fixtures import tomorrowio_config_entry_update, tomorrowio_config_flow_connect
from .const import API_KEY, MIN_CONFIG

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _connect: None = Depends(tomorrowio_config_flow_connect),
    _entry_update: None = Depends(tomorrowio_config_entry_update),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow_minimum_fields(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user config flow with minimum fields."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=_get_config_schema(hass, SOURCE_USER, MIN_CONFIG)(MIN_CONFIG),
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"][CONF_NAME]).to_equal(DEFAULT_NAME)
    expect(result["data"][CONF_API_KEY]).to_equal(API_KEY)
    expect(result["data"][CONF_LOCATION][CONF_LATITUDE]).to_equal(hass.config.latitude)
    expect(result["data"][CONF_LOCATION][CONF_LONGITUDE]).to_equal(hass.config.longitude)


@test
async def user_flow_minimum_fields_in_zone(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user config flow with minimum fields."""
    expect(
        bool(
            await async_setup_component(
                hass,
                "zone",
                {
                    "zone": {
                        CONF_NAME: "Home",
                        CONF_LATITUDE: hass.config.latitude,
                        CONF_LONGITUDE: hass.config.longitude,
                        CONF_RADIUS: 100,
                    }
                },
            )
        )
    ).to_be(True)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=_get_config_schema(hass, SOURCE_USER, MIN_CONFIG)(MIN_CONFIG),
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"{DEFAULT_NAME} - Home")
    expect(result["data"][CONF_NAME]).to_equal(f"{DEFAULT_NAME} - Home")
    expect(result["data"][CONF_API_KEY]).to_equal(API_KEY)
    expect(result["data"][CONF_LOCATION][CONF_LATITUDE]).to_equal(hass.config.latitude)
    expect(result["data"][CONF_LOCATION][CONF_LONGITUDE]).to_equal(hass.config.longitude)


@test
async def user_flow_same_unique_ids(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user config flow with the same unique ID as an existing entry."""
    user_input = _get_config_schema(hass, SOURCE_USER, MIN_CONFIG)(MIN_CONFIG)
    MockConfigEntry(
        domain=DOMAIN,
        data=user_input,
        options={CONF_TIMESTEP: DEFAULT_TIMESTEP},
        source=SOURCE_USER,
        unique_id=_get_unique_id(hass, user_input),
        version=2,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=user_input,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user config flow when Tomorrow.io can't connect."""
    with patch(
        "homeassistant.components.tomorrowio.config_flow.TomorrowioV4.realtime",
        side_effect=CantConnectException,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=_get_config_schema(hass, SOURCE_USER, MIN_CONFIG)(MIN_CONFIG),
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def user_flow_invalid_api(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user config flow when API key is invalid."""
    with patch(
        "homeassistant.components.tomorrowio.config_flow.TomorrowioV4.realtime",
        side_effect=InvalidAPIKeyException,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=_get_config_schema(hass, SOURCE_USER, MIN_CONFIG)(MIN_CONFIG),
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({CONF_API_KEY: "invalid_api_key"})


@test
async def user_flow_rate_limited(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user config flow when API key is rate limited."""
    with patch(
        "homeassistant.components.tomorrowio.config_flow.TomorrowioV4.realtime",
        side_effect=RateLimitedException,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=_get_config_schema(hass, SOURCE_USER, MIN_CONFIG)(MIN_CONFIG),
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({CONF_API_KEY: "rate_limited"})


@test
async def user_flow_unknown_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user config flow when unknown error occurs."""
    with patch(
        "homeassistant.components.tomorrowio.config_flow.TomorrowioV4.realtime",
        side_effect=UnknownException,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=_get_config_schema(hass, SOURCE_USER, MIN_CONFIG)(MIN_CONFIG),
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "unknown"})


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options config flow for tomorrowio."""
    user_config = _get_config_schema(hass, SOURCE_USER)(MIN_CONFIG)
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=user_config,
        options={CONF_TIMESTEP: DEFAULT_TIMESTEP},
        source=SOURCE_USER,
        unique_id=_get_unique_id(hass, user_config),
        version=1,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)

    expect(entry.options[CONF_TIMESTEP]).to_equal(DEFAULT_TIMESTEP)
    expect(CONF_TIMESTEP not in entry.data).to_be(True)

    result = await hass.config_entries.options.async_init(entry.entry_id, data=None)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_TIMESTEP: 1}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("")
    expect(result["data"][CONF_TIMESTEP]).to_equal(1)
    expect(entry.options[CONF_TIMESTEP]).to_equal(1)
