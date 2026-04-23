"""Tryke fixtures for NextBus config_flow tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

from tryke import Depends, fixture

DIRECTIONS_OUTBOUND_HIDDEN: list[dict[str, Any]] = [
    {
        "name": "Outbound",
        "shortName": "Outbound",
        "useForUi": True,
        "stops": ["5184"],
    },
    {
        "name": "Outbound - Hidden",
        "shortName": "Outbound - Hidden",
        "useForUi": False,
        "stops": ["5651"],
    },
]

DIRECTIONS_BOTH: list[dict[str, Any]] = [
    {
        "name": "Outbound",
        "shortName": "Outbound",
        "useForUi": True,
        "stops": ["5184"],
    },
    {
        "name": "Inbound",
        "shortName": "Inbound",
        "useForUi": True,
        "stops": ["5651"],
    },
]


@fixture
def mock_setup_entry() -> Generator[MagicMock]:
    """Create a mock for the nextbus component setup."""
    with patch(
        "homeassistant.components.nextbus.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock


@fixture
def mock_nextbus() -> Generator[MagicMock]:
    """Create a mock py_nextbus module."""
    with patch(
        "homeassistant.components.nextbus.config_flow.NextBusClient"
    ) as client:
        yield client


def make_mock_nextbus_lists(
    client: MagicMock, directions: list[dict[str, Any]]
) -> MagicMock:
    """Configure a mock NextBusClient with list responses."""
    instance = client.return_value
    instance.agencies.return_value = [
        {
            "id": "sfmta-cis",
            "name": "San Francisco Muni CIS",
            "shortName": "SF Muni CIS",
            "region": "",
            "website": "",
            "logo": "",
            "nxbs2RedirectUrl": "",
        }
    ]
    instance.routes.return_value = [
        {
            "id": "F",
            "rev": 1057,
            "title": "F Market & Wharves",
            "description": "7am-10pm daily",
            "color": "",
            "textColor": "",
            "hidden": False,
            "timestamp": "2024-06-23T03:06:58Z",
        },
        {
            "id": "G",
            "rev": 1057,
            "title": "F Market & Wharves",
            "description": "7am-10pm daily",
            "color": "",
            "textColor": "",
            "hidden": False,
            "timestamp": "2024-06-23T03:06:58Z",
        },
    ]

    def route_details_side_effect(agency: str, route: str) -> dict[str, Any]:
        route = route.upper()
        return {
            "id": route,
            "rev": 1057,
            "title": f"{route} Market & Wharves",
            "description": "7am-10pm daily",
            "color": "",
            "textColor": "",
            "hidden": False,
            "boundingBox": {},
            "stops": [
                {
                    "id": "5184",
                    "lat": 37.8071299,
                    "lon": -122.41732,
                    "name": "Jones St & Beach St",
                    "code": "15184",
                    "hidden": False,
                    "showDestinationSelector": True,
                    "directions": ["F_0_var1", "F_0_var0"],
                },
                {
                    "id": "5651",
                    "lat": 37.8071299,
                    "lon": -122.41732,
                    "name": "Jones St & Beach St",
                    "code": "15651",
                    "hidden": False,
                    "showDestinationSelector": True,
                    "directions": ["F_0_var1", "F_0_var0"],
                },
            ],
            "directions": directions,
            "paths": [],
            "timestamp": "2024-06-23T03:06:58Z",
        }

    instance.route_details.side_effect = route_details_side_effect
    return instance
