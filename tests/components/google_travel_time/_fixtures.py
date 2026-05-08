"""Tryke fixtures for the google_travel_time integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from google.maps.routing_v2 import ComputeRoutesResponse, Route
from google.protobuf import duration_pb2
from google.type import localized_text_pb2
from tryke import Depends, fixture

from homeassistant.components.google_travel_time.const import DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_setup_entry() -> Generator[None]:
    """Bypass entry setup."""
    with patch(
        "homeassistant.components.google_travel_time.async_setup_entry",
        return_value=True,
    ):
        yield


@fixture
def routes_mock() -> Generator[AsyncMock]:
    """Return valid API result."""
    with (
        patch(
            "homeassistant.components.google_travel_time.helpers.RoutesAsyncClient",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.google_travel_time.sensor.RoutesAsyncClient",
            new=mock_client,
        ),
        patch(
            "homeassistant.components.google_travel_time.services.RoutesAsyncClient",
            new=mock_client,
        ),
    ):
        client_mock = mock_client.return_value
        client_mock.compute_routes.return_value = ComputeRoutesResponse(
            mapping={
                "routes": [
                    Route(
                        mapping={
                            "localized_values": Route.RouteLocalizedValues(
                                mapping={
                                    "distance": localized_text_pb2.LocalizedText(
                                        text="21.3 km"
                                    ),
                                    "duration": localized_text_pb2.LocalizedText(
                                        text="27 mins"
                                    ),
                                    "static_duration": localized_text_pb2.LocalizedText(
                                        text="26 mins"
                                    ),
                                }
                            ),
                            "distance_meters": 21300,
                            "duration": duration_pb2.Duration(seconds=27 * 60),
                            "static_duration": duration_pb2.Duration(seconds=26 * 60),
                        }
                    )
                ]
            }
        )
        yield client_mock


@fixture
async def make_mock_config(
    hass: HomeAssistant = Depends(hass_fixture),
):
    """Return a factory for setting up a config entry."""

    async def _make(data: dict, options: dict) -> MockConfigEntry:
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data=data,
            options=options,
            entry_id="test",
        )
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        return config_entry

    return _make
