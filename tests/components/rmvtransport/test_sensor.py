"""The tests for the rmvtransport platform."""

import datetime
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture, mock_network

VALID_CONFIG_MINIMAL = {
    "sensor": {"platform": "rmvtransport", "next_departure": [{"station": "3000010"}]}
}

VALID_CONFIG_NAME = {
    "sensor": {
        "platform": "rmvtransport",
        "next_departure": [{"station": "3000010", "name": "My Station"}],
    }
}

VALID_CONFIG_MISC = {
    "sensor": {
        "platform": "rmvtransport",
        "next_departure": [
            {
                "station": "3000010",
                "lines": [21, "S8"],
                "max_journeys": 2,
                "time_offset": 10,
            }
        ],
    }
}

VALID_CONFIG_DEST = {
    "sensor": {
        "platform": "rmvtransport",
        "next_departure": [
            {
                "station": "3000010",
                "destinations": [
                    "Frankfurt (Main) Flughafen Regionalbahnhof",
                    "Frankfurt (Main) Stadion",
                ],
                "lines": [12, "S8"],
                "time_offset": 15,
            }
        ],
    }
}

VALID_CONFIG_DEST_ONLY = {
    "sensor": {
        "platform": "rmvtransport",
        "next_departure": [
            {
                "station": "3000010",
                "destinations": [
                    "Frankfurt (Main) Flughafen Regionalbahnhof",
                    "Frankfurt (Main) Stadion",
                ],
            }
        ],
    }
}


def get_departures_mock():
    """Mock rmvtransport departures loading."""
    return {
        "station": "Frankfurt (Main) Hauptbahnhof",
        "stationId": "3000010",
        "filter": "11111111111",
        "journeys": [
            {
                "product": "Tram",
                "number": 12,
                "trainId": "1123456",
                "direction": "Frankfurt (Main) Hugo-Junkers-Straße/Schleife",
                "departure_time": datetime.datetime(2018, 8, 6, 14, 21),
                "minutes": 7,
                "delay": 3,
                "stops": [
                    "Frankfurt (Main) Willy-Brandt-Platz",
                    "Frankfurt (Main) Römer/Paulskirche",
                    "Frankfurt (Main) Börneplatz",
                    "Frankfurt (Main) Konstablerwache",
                    "Frankfurt (Main) Bornheim Mitte",
                    "Frankfurt (Main) Saalburg-/Wittelsbacherallee",
                    "Frankfurt (Main) Eissporthalle/Festplatz",
                    "Frankfurt (Main) Hugo-Junkers-Straße/Schleife",
                ],
                "info": None,
                "info_long": None,
                "icon": "https://products/32_pic.png",
            },
            {
                "product": "Bus",
                "number": 21,
                "trainId": "1234567",
                "direction": "Frankfurt (Main) Hugo-Junkers-Straße/Schleife",
                "departure_time": datetime.datetime(2018, 8, 6, 14, 22),
                "minutes": 8,
                "delay": 1,
                "stops": [
                    "Frankfurt (Main) Weser-/Münchener Straße",
                    "Frankfurt (Main) Hugo-Junkers-Straße/Schleife",
                ],
                "info": None,
                "info_long": None,
                "icon": "https://products/32_pic.png",
            },
            {
                "product": "Bus",
                "number": 12,
                "trainId": "1234568",
                "direction": "Frankfurt (Main) Hugo-Junkers-Straße/Schleife",
                "departure_time": datetime.datetime(2018, 8, 6, 14, 25),
                "minutes": 11,
                "delay": 1,
                "stops": ["Frankfurt (Main) Stadion"],
                "info": None,
                "info_long": None,
                "icon": "https://products/32_pic.png",
            },
            {
                "product": "Bus",
                "number": 21,
                "trainId": "1234569",
                "direction": "Frankfurt (Main) Hugo-Junkers-Straße/Schleife",
                "departure_time": datetime.datetime(2018, 8, 6, 14, 25),
                "minutes": 11,
                "delay": 1,
                "stops": [],
                "info": None,
                "info_long": None,
                "icon": "https://products/32_pic.png",
            },
            {
                "product": "Bus",
                "number": 12,
                "trainId": "1234570",
                "direction": "Frankfurt (Main) Hugo-Junkers-Straße/Schleife",
                "departure_time": datetime.datetime(2018, 8, 6, 14, 25),
                "minutes": 11,
                "delay": 1,
                "stops": [],
                "info": None,
                "info_long": None,
                "icon": "https://products/32_pic.png",
            },
            {
                "product": "Bus",
                "number": 21,
                "trainId": "1234571",
                "direction": "Frankfurt (Main) Hugo-Junkers-Straße/Schleife",
                "departure_time": datetime.datetime(2018, 8, 6, 14, 25),
                "minutes": 11,
                "delay": 1,
                "stops": [],
                "info": None,
                "info_long": None,
                "icon": "https://products/32_pic.png",
            },
            {
                "product": "Bus",
                "number": 12,
                "trainId": "1234568",
                "direction": "Frankfurt (Main) Hugo-Junkers-Straße/Schleife",
                "departure_time": datetime.datetime(2018, 8, 6, 14, 30),
                "minutes": 16,
                "delay": 0,
                "stops": ["Frankfurt (Main) Stadion"],
                "info": None,
                "info_long": None,
                "icon": "https://products/32_pic.png",
            },
        ],
    }


def get_no_departures_mock():
    """Mock no departures in results."""
    return {
        "station": "Frankfurt (Main) Hauptbahnhof",
        "stationId": "3000010",
        "filter": "11111111111",
        "journeys": [],
    }


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def rmvtransport_min_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test minimal rmvtransport configuration."""
    with patch(
        "RMVtransport.RMVtransport.get_departures",
        return_value=get_departures_mock(),
    ):
        expect(
            await async_setup_component(hass, "sensor", VALID_CONFIG_MINIMAL) is True
        ).to_be(True)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.frankfurt_main_hauptbahnhof")
    expect(state.state).to_equal("7")
    expect(state.attributes["departure_time"]).to_equal(
        datetime.datetime(2018, 8, 6, 14, 21)
    )
    expect(state.attributes["direction"]).to_equal(
        "Frankfurt (Main) Hugo-Junkers-Straße/Schleife"
    )
    expect(state.attributes["product"]).to_equal("Tram")
    expect(state.attributes["line"]).to_equal(12)
    expect(state.attributes["icon"]).to_equal("mdi:tram")
    expect(state.attributes["friendly_name"]).to_equal(
        "Frankfurt (Main) Hauptbahnhof"
    )


@test
async def rmvtransport_name_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test custom name configuration."""
    with patch(
        "RMVtransport.RMVtransport.get_departures",
        return_value=get_departures_mock(),
    ):
        expect(
            bool(await async_setup_component(hass, "sensor", VALID_CONFIG_NAME))
        ).to_be(True)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.my_station")
    expect(state.attributes["friendly_name"]).to_equal("My Station")


@test
async def rmvtransport_misc_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test misc configuration."""
    with patch(
        "RMVtransport.RMVtransport.get_departures",
        return_value=get_departures_mock(),
    ):
        expect(
            bool(await async_setup_component(hass, "sensor", VALID_CONFIG_MISC))
        ).to_be(True)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.frankfurt_main_hauptbahnhof")
    expect(state.attributes["friendly_name"]).to_equal(
        "Frankfurt (Main) Hauptbahnhof"
    )
    expect(state.attributes["line"]).to_equal(21)


@test
async def rmvtransport_dest_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test destination configuration."""
    with patch(
        "RMVtransport.RMVtransport.get_departures",
        return_value=get_departures_mock(),
    ):
        expect(
            bool(await async_setup_component(hass, "sensor", VALID_CONFIG_DEST))
        ).to_be(True)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.frankfurt_main_hauptbahnhof")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("16")
    expect(state.attributes["direction"]).to_equal(
        "Frankfurt (Main) Hugo-Junkers-Straße/Schleife"
    )
    expect(state.attributes["line"]).to_equal(12)
    expect(state.attributes["minutes"]).to_equal(16)
    expect(state.attributes["departure_time"]).to_equal(
        datetime.datetime(2018, 8, 6, 14, 30)
    )


@test
async def rmvtransport_dest_only_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test destination configuration."""
    with patch(
        "RMVtransport.RMVtransport.get_departures",
        return_value=get_departures_mock(),
    ):
        expect(
            bool(await async_setup_component(hass, "sensor", VALID_CONFIG_DEST_ONLY))
        ).to_be(True)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.frankfurt_main_hauptbahnhof")
    expect(state.state).to_equal("11")
    expect(state.attributes["direction"]).to_equal(
        "Frankfurt (Main) Hugo-Junkers-Straße/Schleife"
    )
    expect(state.attributes["line"]).to_equal(12)
    expect(state.attributes["minutes"]).to_equal(11)
    expect(state.attributes["departure_time"]).to_equal(
        datetime.datetime(2018, 8, 6, 14, 25)
    )


@test
async def rmvtransport_no_departures(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for no departures."""
    with patch(
        "RMVtransport.RMVtransport.get_departures",
        return_value=get_no_departures_mock(),
    ):
        expect(
            bool(await async_setup_component(hass, "sensor", VALID_CONFIG_MINIMAL))
        ).to_be(True)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.frankfurt_main_hauptbahnhof")
    expect(state.state).to_equal("unavailable")
