"""Test the HVV Departures config flow."""

import json
from unittest.mock import patch

from pygti.exceptions import CannotConnect, InvalidAuth
from tryke import Depends, expect, fixture, test

from homeassistant.components.hvv_departures.const import (
    CONF_FILTER,
    CONF_REAL_TIME,
    CONF_STATION,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_OFFSET, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry, load_fixture
from tests.hass_fixtures import hass as hass_fixture, mock_network

FIXTURE_INIT = json.loads(load_fixture("hvv_departures/init.json"))
FIXTURE_CHECK_NAME = json.loads(load_fixture("hvv_departures/check_name.json"))
FIXTURE_STATION_INFORMATION = json.loads(
    load_fixture("hvv_departures/station_information.json")
)
FIXTURE_CONFIG_ENTRY = json.loads(load_fixture("hvv_departures/config_entry.json"))
FIXTURE_OPTIONS = json.loads(load_fixture("hvv_departures/options.json"))
FIXTURE_DEPARTURE_LIST = json.loads(load_fixture("hvv_departures/departure_list.json"))


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that config flow works."""
    with (
        patch(
            "homeassistant.components.hvv_departures.hub.GTI.init",
            return_value=FIXTURE_INIT,
        ),
        patch(
            "homeassistant.components.hvv_departures.hub.GTI.checkName",
            return_value=FIXTURE_CHECK_NAME,
        ),
        patch(
            "homeassistant.components.hvv_departures.hub.GTI.stationInformation",
            return_value=FIXTURE_STATION_INFORMATION,
        ),
        patch(
            "homeassistant.components.hvv_departures.async_setup_entry",
            return_value=True,
        ),
    ):
        # Step: user.
        result_user = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_HOST: "api-test.geofox.de",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

        expect(result_user["step_id"]).to_equal("station")

        # Step: station.
        result_station = await hass.config_entries.flow.async_configure(
            result_user["flow_id"],
            {CONF_STATION: "Wartenau"},
        )

        expect(result_station["step_id"]).to_equal("station_select")

        # Step: station_select.
        result_station_select = await hass.config_entries.flow.async_configure(
            result_user["flow_id"],
            {CONF_STATION: "Wartenau"},
        )

        expect(result_station_select["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result_station_select["title"]).to_equal("Wartenau")
        expect(result_station_select["data"]).to_equal(
            {
                CONF_HOST: "api-test.geofox.de",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_STATION: {
                    "name": "Wartenau",
                    "city": "Hamburg",
                    "combinedName": "Wartenau",
                    "id": "Master:10901",
                    "type": "STATION",
                    "coordinate": {"x": 10.035515, "y": 53.56478},
                    "serviceTypes": ["bus", "u"],
                    "hasStationInformation": True,
                },
            }
        )


@test
async def user_flow_no_results(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that config flow works when there are no results."""
    with (
        patch(
            "homeassistant.components.hvv_departures.hub.GTI.init",
            return_value=FIXTURE_INIT,
        ),
        patch(
            "homeassistant.components.hvv_departures.hub.GTI.checkName",
            return_value={"returnCode": "OK", "results": []},
        ),
        patch(
            "homeassistant.components.hvv_departures.async_setup_entry",
            return_value=True,
        ),
    ):
        # Step: user.
        result_user = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_HOST: "api-test.geofox.de",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

        expect(result_user["step_id"]).to_equal("station")

        # Step: station.
        result_station = await hass.config_entries.flow.async_configure(
            result_user["flow_id"],
            {CONF_STATION: "non_existing_station"},
        )

        expect(result_station["step_id"]).to_equal("station")
        expect(result_station["errors"]["base"]).to_equal("no_results")


@test
async def user_flow_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that config flow handles invalid auth."""
    with patch(
        "homeassistant.components.hvv_departures.hub.GTI.init",
        side_effect=InvalidAuth(
            "ERROR_TEXT",
            "Bei der Verarbeitung der Anfrage ist ein technisches Problem aufgetreten.",  # codespell:ignore ist
            "Authentication failed!",
        ),
    ):
        # Step: user.
        result_user = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_HOST: "api-test.geofox.de",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

        expect(result_user["type"]).to_be(FlowResultType.FORM)
        expect(result_user["errors"]).to_equal({"base": "invalid_auth"})


@test
async def user_flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that config flow handles connection errors."""
    with patch(
        "homeassistant.components.hvv_departures.hub.GTI.init",
        side_effect=CannotConnect(),
    ):
        # Step: user.
        result_user = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_HOST: "api-test.geofox.de",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

        expect(result_user["type"]).to_be(FlowResultType.FORM)
        expect(result_user["errors"]).to_equal({"base": "cannot_connect"})


@test
async def user_flow_station(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that config flow handles empty data on step station."""
    with (
        patch(
            "homeassistant.components.hvv_departures.hub.GTI.init",
            return_value=True,
        ),
        patch(
            "homeassistant.components.hvv_departures.hub.GTI.checkName",
            return_value={"returnCode": "OK", "results": []},
        ),
    ):
        # Step: user.
        result_user = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_HOST: "api-test.geofox.de",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

        expect(result_user["step_id"]).to_equal("station")

        # Step: station.
        result_station = await hass.config_entries.flow.async_configure(
            result_user["flow_id"],
            None,
        )
        expect(result_station["type"]).to_be(FlowResultType.FORM)
        expect(result_station["step_id"]).to_equal("station")


@test
async def user_flow_station_select(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that config flow handles empty data on step station_select."""
    with (
        patch(
            "homeassistant.components.hvv_departures.hub.GTI.init",
            return_value=True,
        ),
        patch(
            "homeassistant.components.hvv_departures.hub.GTI.checkName",
            return_value=FIXTURE_CHECK_NAME,
        ),
    ):
        result_user = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_HOST: "api-test.geofox.de",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

        result_station = await hass.config_entries.flow.async_configure(
            result_user["flow_id"],
            {CONF_STATION: "Wartenau"},
        )

        # Step: station_select.
        result_station_select = await hass.config_entries.flow.async_configure(
            result_station["flow_id"],
            None,
        )

        expect(result_station_select["type"]).to_be(FlowResultType.FORM)
        expect(result_station_select["step_id"]).to_equal("station_select")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that options flow works."""
    config_entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Wartenau",
        data=FIXTURE_CONFIG_ENTRY,
        source=SOURCE_USER,
        options=FIXTURE_OPTIONS,
        unique_id="1234",
    )
    config_entry.add_to_hass(hass)

    with (
        patch("homeassistant.components.hvv_departures.PLATFORMS", new=[]),
        patch(
            "homeassistant.components.hvv_departures.hub.GTI.init",
            return_value=True,
        ),
        patch(
            "homeassistant.components.hvv_departures.hub.GTI.departureList",
            return_value=FIXTURE_DEPARTURE_LIST,
        ),
    ):
        expect(
            await hass.config_entries.async_setup(config_entry.entry_id)
        ).to_be(True)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(config_entry.entry_id)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_FILTER: ["0"], CONF_OFFSET: 15, CONF_REAL_TIME: False},
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(config_entry.options).to_equal(
            {
                CONF_FILTER: [
                    {
                        "serviceID": "HHA-U:U1_HHA-U",
                        "stationIDs": ["Master:10902"],
                        "label": "Fuhlsbüttel Nord / Ochsenzoll / Norderstedt Mitte / Kellinghusenstraße / Ohlsdorf / Garstedt",
                        "serviceName": "U1",
                    }
                ],
                CONF_OFFSET: 15,
                CONF_REAL_TIME: False,
            }
        )


@test
async def options_flow_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that options flow works."""
    config_entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Wartenau",
        data=FIXTURE_CONFIG_ENTRY,
        source=SOURCE_USER,
        options=FIXTURE_OPTIONS,
        unique_id="1234",
    )
    config_entry.add_to_hass(hass)

    with (
        patch("homeassistant.components.hvv_departures.PLATFORMS", new=[]),
        patch(
            "homeassistant.components.hvv_departures.hub.GTI.init", return_value=True
        ),
        patch(
            "homeassistant.components.hvv_departures.hub.GTI.departureList",
            return_value=FIXTURE_DEPARTURE_LIST,
        ),
    ):
        expect(
            await hass.config_entries.async_setup(config_entry.entry_id)
        ).to_be(True)
        await hass.async_block_till_done()

    with patch(
        "homeassistant.components.hvv_departures.hub.GTI.departureList",
        side_effect=InvalidAuth(
            "ERROR_TEXT",
            "Bei der Verarbeitung der Anfrage ist ein technisches Problem aufgetreten.",  # codespell:ignore ist
            "Authentication failed!",
        ),
    ):
        result = await hass.config_entries.options.async_init(config_entry.entry_id)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        expect(result["errors"]).to_equal({"base": "invalid_auth"})


@test
async def options_flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that options flow works."""
    config_entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Wartenau",
        data=FIXTURE_CONFIG_ENTRY,
        source=SOURCE_USER,
        options=FIXTURE_OPTIONS,
        unique_id="1234",
    )
    config_entry.add_to_hass(hass)

    with (
        patch("homeassistant.components.hvv_departures.PLATFORMS", new=[]),
        patch(
            "homeassistant.components.hvv_departures.hub.GTI.init", return_value=True
        ),
        patch(
            "homeassistant.components.hvv_departures.hub.GTI.departureList",
            return_value=FIXTURE_DEPARTURE_LIST,
        ),
    ):
        expect(
            await hass.config_entries.async_setup(config_entry.entry_id)
        ).to_be(True)
        await hass.async_block_till_done()

    with patch(
        "homeassistant.components.hvv_departures.hub.GTI.departureList",
        side_effect=CannotConnect(),
    ):
        result = await hass.config_entries.options.async_init(config_entry.entry_id)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        expect(result["errors"]).to_equal({"base": "cannot_connect"})
