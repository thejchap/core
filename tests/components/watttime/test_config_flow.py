"""Test the WattTime config flow."""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from aiowatttime.errors import CoordinatesNotFoundError, InvalidCredentialsError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.watttime.config_flow import (
    CONF_LOCATION_TYPE,
    LOCATION_TYPE_HOME,
)
from homeassistant.components.watttime.const import (
    CONF_BALANCING_AUTHORITY,
    CONF_BALANCING_AUTHORITY_ABBREV,
    DOMAIN,
)
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_PASSWORD,
    CONF_SHOW_ON_MAP,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    client as client_fx,
    config_auth as config_auth_fx,
    config_coordinates as config_coordinates_fx,
    config_location_type as config_location_type_fx,
    make_config_entry,
    setup_watttime,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.cases(
    test.case("invalid_auth", exc=InvalidCredentialsError, error="invalid_auth"),
    test.case("unknown", exc=Exception, error="unknown"),
)
async def auth_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_auth: dict[str, Any] = Depends(config_auth_fx),
    *,
    exc: type[Exception],
    error: str,
) -> None:
    """Test that issues with auth show the correct error."""
    with patch(
        "homeassistant.components.watttime.config_flow.Client.async_login",
        side_effect=exc,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=config_auth
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": error})


@test.cases(
    test.case(
        "coordinates_not_found",
        side_effect=CoordinatesNotFoundError,
        errors={"latitude": "unknown_coordinates"},
    ),
    test.case("unknown", side_effect=Exception, errors={"base": "unknown"}),
)
async def coordinate_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_auth: dict[str, Any] = Depends(config_auth_fx),
    config_coordinates: dict[str, Any] = Depends(config_coordinates_fx),
    config_location_type: dict[str, Any] = Depends(config_location_type_fx),
    client: Mock = Depends(client_fx),
    *,
    side_effect: type[Exception],
    errors: dict[str, str],
) -> None:
    """Test that issues with coordinates show the correct error."""
    client.emissions.async_get_grid_region = AsyncMock(side_effect=side_effect)
    async with setup_watttime(hass, client, config_auth, config_coordinates):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=config_auth
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=config_location_type
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=config_coordinates
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal(errors)


@test
async def duplicate_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_auth: dict[str, Any] = Depends(config_auth_fx),
    config_coordinates: dict[str, Any] = Depends(config_coordinates_fx),
    client: Mock = Depends(client_fx),
) -> None:
    """Test that errors are shown when duplicate entries are added."""
    config_entry = make_config_entry(config_auth, config_coordinates)
    config_entry.add_to_hass(hass)
    config_location_type = {CONF_LOCATION_TYPE: LOCATION_TYPE_HOME}

    async with setup_watttime(hass, client, config_auth, config_coordinates):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=config_auth
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=config_location_type
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_auth: dict[str, Any] = Depends(config_auth_fx),
    config_coordinates: dict[str, Any] = Depends(config_coordinates_fx),
) -> None:
    """Test config flow options."""
    config_entry = make_config_entry(config_auth, config_coordinates)
    config_entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.watttime.async_setup_entry", return_value=True
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input={CONF_SHOW_ON_MAP: False}
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(config_entry.options).to_equal({CONF_SHOW_ON_MAP: False})


@test
async def show_form_coordinates(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_auth: dict[str, Any] = Depends(config_auth_fx),
    config_coordinates: dict[str, Any] = Depends(config_coordinates_fx),
    config_location_type: dict[str, Any] = Depends(config_location_type_fx),
    client: Mock = Depends(client_fx),
) -> None:
    """Test showing the form to input custom latitude/longitude."""
    async with setup_watttime(hass, client, config_auth, config_coordinates):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=config_auth
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=config_location_type
        )
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("coordinates")
        expect(result["errors"]).to_be(None)


@test
async def show_form_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test showing the form to select the authentication type."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_be(None)


@test
async def step_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_auth: dict[str, Any] = Depends(config_auth_fx),
    config_coordinates: dict[str, Any] = Depends(config_coordinates_fx),
    client: Mock = Depends(client_fx),
) -> None:
    """Test a full reauth flow."""
    config_entry = make_config_entry(config_auth, config_coordinates)
    config_entry.add_to_hass(hass)
    async with setup_watttime(hass, client, config_auth, config_coordinates):
        result = await config_entry.start_reauth_flow(hass)
        with patch(
            "homeassistant.components.watttime.async_setup_entry",
            return_value=True,
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={CONF_PASSWORD: "password"},
            )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("reauth_successful")
        expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def step_user_coordinates(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_auth: dict[str, Any] = Depends(config_auth_fx),
    config_coordinates: dict[str, Any] = Depends(config_coordinates_fx),
    config_location_type: dict[str, Any] = Depends(config_location_type_fx),
    client: Mock = Depends(client_fx),
) -> None:
    """Test a full login flow (inputting custom coordinates)."""
    async with setup_watttime(hass, client, config_auth, config_coordinates):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=config_auth
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=config_location_type
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=config_coordinates
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("32.87336, -117.22743")
        expect(result["data"]).to_equal(
            {
                CONF_USERNAME: "user",
                CONF_PASSWORD: "password",
                CONF_LATITUDE: 32.87336,
                CONF_LONGITUDE: -117.22743,
                CONF_BALANCING_AUTHORITY: "PJM New Jersey",
                CONF_BALANCING_AUTHORITY_ABBREV: "PJM_NJ",
            }
        )


@test
async def step_user_home(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_auth: dict[str, Any] = Depends(config_auth_fx),
    config_coordinates: dict[str, Any] = Depends(config_coordinates_fx),
    client: Mock = Depends(client_fx),
) -> None:
    """Test a full login flow (selecting the home location)."""
    config_location_type = {CONF_LOCATION_TYPE: LOCATION_TYPE_HOME}
    async with setup_watttime(hass, client, config_auth, config_coordinates):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=config_auth
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=config_location_type
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("32.87336, -117.22743")
        expect(result["data"]).to_equal(
            {
                CONF_USERNAME: "user",
                CONF_PASSWORD: "password",
                CONF_LATITUDE: 32.87336,
                CONF_LONGITUDE: -117.22743,
                CONF_BALANCING_AUTHORITY: "PJM New Jersey",
                CONF_BALANCING_AUTHORITY_ABBREV: "PJM_NJ",
            }
        )
