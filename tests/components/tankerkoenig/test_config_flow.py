"""Tests for Tankerkoenig config flow."""

from unittest.mock import AsyncMock, patch

from aiotankerkoenig.exceptions import TankerkoenigInvalidKeyError
from tryke import Depends, expect, fixture, test

from homeassistant.components.tankerkoenig.const import CONF_STATIONS, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_RADIUS,
    CONF_SHOW_ON_MAP,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from ._fixtures import config_entry as config_entry_fixture, tankerkoenig
from .const import NEARBY_STATIONS

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_USER_DATA = {
    CONF_NAME: "Home",
    CONF_API_KEY: "269534f6-xxxx-xxxx-xxxx-yyyyzzzzxxxx",
    CONF_LOCATION: {CONF_LATITUDE: 51.0, CONF_LONGITUDE: 13.0},
    CONF_RADIUS: 2.0,
}

MOCK_STATIONS_DATA = {
    CONF_STATIONS: [
        "3bcd61da-xxxx-xxxx-xxxx-19d5523a7ae8",
        "36b4b812-xxxx-xxxx-xxxx-c51735325858",
    ],
}

MOCK_OPTIONS_DATA = {
    **MOCK_USER_DATA,
    CONF_STATIONS: [
        "3bcd61da-xxxx-xxxx-xxxx-19d5523a7ae8",
        "36b4b812-xxxx-xxxx-xxxx-c51735325858",
        "54e2b642-xxxx-xxxx-xxxx-87cd4e9867f1",
    ],
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test starting a flow by user."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "homeassistant.components.tankerkoenig.async_setup_entry", return_value=True
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.tankerkoenig.config_flow.Tankerkoenig.nearby_stations",
            return_value=NEARBY_STATIONS,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("select_station")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_STATIONS_DATA
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["data"][CONF_NAME]).to_equal("Home")
        expect(result["data"][CONF_API_KEY]).to_equal(
            "269534f6-xxxx-xxxx-xxxx-yyyyzzzzxxxx"
        )
        expect(result["data"][CONF_LOCATION]).to_equal(
            {"latitude": 51.0, "longitude": 13.0}
        )
        expect(result["data"][CONF_RADIUS]).to_equal(2.0)
        expect(result["data"][CONF_STATIONS]).to_equal(
            [
                "3bcd61da-xxxx-xxxx-xxxx-19d5523a7ae8",
                "36b4b812-xxxx-xxxx-xxxx-c51735325858",
            ]
        )
        expect(bool(result["options"][CONF_SHOW_ON_MAP])).to_be(True)

        await hass.async_block_till_done()

    expect(bool(mock_setup_entry.called)).to_be(True)


@test
async def user_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test starting a flow by user with an already configured region."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        data={**MOCK_USER_DATA, **MOCK_STATIONS_DATA},
        unique_id=f"{MOCK_USER_DATA[CONF_LOCATION][CONF_LATITUDE]}_{MOCK_USER_DATA[CONF_LOCATION][CONF_LONGITUDE]}",
    )
    mock_config.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_USER_DATA
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def exception_security(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test starting a flow by user with invalid api key."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.tankerkoenig.config_flow.Tankerkoenig.nearby_stations",
        side_effect=TankerkoenigInvalidKeyError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"][CONF_API_KEY]).to_equal("invalid_auth")


@test
async def user_no_stations(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test starting a flow by user which does not find any station."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.tankerkoenig.config_flow.Tankerkoenig.nearby_stations",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"][CONF_RADIUS]).to_equal("no_stations")


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
) -> None:
    """Test starting a flow by user to re-auth."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with (
        patch(
            "homeassistant.components.tankerkoenig.async_setup_entry", return_value=True
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.tankerkoenig.config_flow.Tankerkoenig.nearby_stations",
        ) as mock_nearby_stations,
    ):
        mock_nearby_stations.side_effect = TankerkoenigInvalidKeyError("Booom!")
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_API_KEY: "269534f6-aaaa-bbbb-cccc-yyyyzzzzxxxx",
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("reauth_confirm")
        expect(result["errors"]).to_equal({CONF_API_KEY: "invalid_auth"})

        mock_nearby_stations.side_effect = None
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_API_KEY: "269534f6-aaaa-bbbb-cccc-yyyyzzzzxxxx",
            },
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("reauth_successful")

    mock_setup_entry.assert_called()

    entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    expect(entry.data[CONF_API_KEY]).to_equal("269534f6-aaaa-bbbb-cccc-yyyyzzzzxxxx")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tankerkoenig: AsyncMock = Depends(tankerkoenig),
) -> None:
    """Test options flow."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_OPTIONS_DATA,
        options={CONF_SHOW_ON_MAP: True},
        unique_id=f"{DOMAIN}_{MOCK_USER_DATA[CONF_LOCATION][CONF_LATITUDE]}_{MOCK_USER_DATA[CONF_LOCATION][CONF_LONGITUDE]}",
    )
    mock_config.add_to_hass(hass)
    expect(bool(await async_setup_component(hass, DOMAIN, {}))).to_be(True)
    await hass.async_block_till_done()

    with (
        patch(
            "homeassistant.components.tankerkoenig.config_flow.Tankerkoenig.nearby_stations",
            return_value=NEARBY_STATIONS,
        ),
        patch(
            "homeassistant.config_entries.ConfigEntries.async_reload"
        ) as mock_async_reload,
    ):
        result = await hass.config_entries.options.async_init(mock_config.entry_id)
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_SHOW_ON_MAP: False,
                CONF_STATIONS: MOCK_OPTIONS_DATA[CONF_STATIONS],
            },
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(bool(mock_config.options[CONF_SHOW_ON_MAP])).to_be(False)

        await hass.async_block_till_done()

        expect(mock_async_reload.call_count).to_equal(1)


@test
async def options_flow_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_OPTIONS_DATA,
        options={CONF_SHOW_ON_MAP: True},
        unique_id=f"{DOMAIN}_{MOCK_USER_DATA[CONF_LOCATION][CONF_LATITUDE]}_{MOCK_USER_DATA[CONF_LOCATION][CONF_LONGITUDE]}",
    )
    mock_config.add_to_hass(hass)

    with patch(
        "homeassistant.components.tankerkoenig.config_flow.Tankerkoenig.nearby_stations",
        side_effect=TankerkoenigInvalidKeyError("Booom!"),
    ) as mock_nearby_stations:
        result = await hass.config_entries.options.async_init(mock_config.entry_id)
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")
        expect(result["errors"]).to_equal({"base": "invalid_auth"})

        mock_nearby_stations.return_value = NEARBY_STATIONS

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_SHOW_ON_MAP: False,
                CONF_STATIONS: MOCK_OPTIONS_DATA[CONF_STATIONS],
            },
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(bool(mock_config.options[CONF_SHOW_ON_MAP])).to_be(False)
