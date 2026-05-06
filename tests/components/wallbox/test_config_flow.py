"""Test the Wallbox config flow."""

from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.wallbox.const import (
    CHARGER_ADDED_ENERGY_KEY,
    CHARGER_ADDED_RANGE_KEY,
    CHARGER_CHARGING_POWER_KEY,
    CHARGER_CHARGING_SPEED_KEY,
    CHARGER_DATA_KEY,
    CHARGER_JWT_REFRESH_TOKEN,
    CHARGER_JWT_TOKEN,
    CHARGER_MAX_AVAILABLE_POWER_KEY,
    CHARGER_MAX_CHARGING_CURRENT_KEY,
    CONF_STATION,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    http_403_error,
    http_404_error,
    make_entry,
    mock_wallbox,
    setup_integration,
)
from .const import WALLBOX_AUTHORISATION_RESPONSE_UNAUTHORISED

from tests.hass_fixtures import hass as hass_fixture, mock_network

test_response = {
    CHARGER_CHARGING_POWER_KEY: 0,
    CHARGER_MAX_AVAILABLE_POWER_KEY: "xx",
    CHARGER_CHARGING_SPEED_KEY: 0,
    CHARGER_ADDED_RANGE_KEY: "xx",
    CHARGER_ADDED_ENERGY_KEY: "44.697",
    CHARGER_DATA_KEY: {CHARGER_MAX_CHARGING_CURRENT_KEY: 24},
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def show_set_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _wb: object = Depends(mock_wallbox),
) -> None:
    """Test that the setup form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def form_cannot_authenticate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with (
        patch(
            "homeassistant.components.wallbox.Wallbox.authenticate",
            new=Mock(side_effect=http_403_error),
        ),
        patch(
            "homeassistant.components.wallbox.Wallbox.pauseChargingSession",
            new=Mock(side_effect=http_403_error),
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_STATION: "12345",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with (
        patch(
            "homeassistant.components.wallbox.Wallbox.authenticate",
            new=Mock(side_effect=http_404_error),
        ),
        patch(
            "homeassistant.components.wallbox.Wallbox.pauseChargingSession",
            new=Mock(side_effect=http_404_error),
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_STATION: "12345",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_validate_input(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    wallbox: object = Depends(mock_wallbox),
) -> None:
    """Test we can validate input."""
    make_entry(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "homeassistant.components.wallbox.config_flow.Wallbox",
        return_value=wallbox,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_STATION: "12345",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    expect(result2["title"]).to_equal("Wallbox Portal")
    expect(result2["data"][CONF_STATION]).to_equal("12345")
    expect(result2["data"][CONF_USERNAME]).to_equal("test-username")
    expect(result2["data"][CHARGER_JWT_TOKEN]).to_equal("test_token")
    expect(result2["data"][CHARGER_JWT_REFRESH_TOKEN]).to_equal("test_refresh_token")


@test
async def form_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    wallbox: object = Depends(mock_wallbox),
) -> None:
    """Test we handle reauth flow."""
    entry = make_entry(hass)
    await setup_integration(hass, entry)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    with (
        patch.object(
            wallbox,
            "authenticate",
            return_value=WALLBOX_AUTHORISATION_RESPONSE_UNAUTHORISED,
        ),
        patch.object(wallbox, "getChargerStatus", return_value=test_response),
    ):
        result = await entry.start_reauth_flow(hass)

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_STATION: "12345",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("reauth_successful")

    await hass.async_block_till_done()
    await hass.config_entries.async_unload(entry.entry_id)


@test
async def form_reauth_invalid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    wallbox: object = Depends(mock_wallbox),
) -> None:
    """Test we handle reauth invalid flow."""
    entry = make_entry(hass)
    await setup_integration(hass, entry)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    with (
        patch.object(
            wallbox,
            "authenticate",
            return_value=WALLBOX_AUTHORISATION_RESPONSE_UNAUTHORISED,
        ),
        patch.object(wallbox, "getChargerStatus", return_value=test_response),
    ):
        result = await entry.start_reauth_flow(hass)

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_STATION: "12345678",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "reauth_invalid"})

    await hass.config_entries.async_unload(entry.entry_id)
