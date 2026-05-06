"""Tryke fixtures for the WSDOT integration."""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture
from wsdot import TravelTime, WsdotTravelError

from homeassistant.components.wsdot.const import DOMAIN
from homeassistant.config_entries import ConfigSubentryData
from homeassistant.const import CONF_API_KEY, CONF_ID, CONF_NAME
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, load_json_object_fixture
from tests.hass_fixtures import hass as hass_fx


@fixture
def mock_travel_time() -> Generator[AsyncMock]:
    """WsdotTravelTimes.get_travel_time is mocked to return TravelTime data."""
    with (
        patch(
            "homeassistant.components.wsdot.wsdot_api.WsdotTravelTimes", autospec=True
        ) as mock,
        patch(
            "homeassistant.components.wsdot.config_flow.wsdot_api.WsdotTravelTimes",
            new=mock,
        ),
    ):
        client = mock.return_value
        response = TravelTime(**load_json_object_fixture("wsdot.json", DOMAIN))
        client.get_travel_time.return_value = response
        client.get_all_travel_times.return_value = [response]
        yield client


@fixture
def mock_failed_travel_time(
    travel_time: AsyncMock = Depends(mock_travel_time),
    *,
    failed_travel_time_status: int = 400,
) -> AsyncMock:
    """WsdotTravelTimes.get_travel_time is mocked to raise a WsdotTravelError."""
    travel_time.get_travel_time.side_effect = WsdotTravelError(
        status=failed_travel_time_status
    )
    travel_time.get_all_travel_times.side_effect = WsdotTravelError(
        status=failed_travel_time_status
    )
    return travel_time


@fixture
def mock_config_data() -> dict[str, Any]:
    """Return valid test config data."""
    return {CONF_API_KEY: "abcd-1234"}


@fixture
def mock_subentries() -> list[ConfigSubentryData]:
    """Mock subentries."""
    return [
        ConfigSubentryData(
            subentry_type="travel_time",
            title="I-90 EB",
            unique_id="96",
            data={
                CONF_ID: 96,
                CONF_NAME: "Seattle-Bellevue via I-90 (EB AM)",
            },
        )
    ]


@fixture
def mock_config_entry(
    config_data: dict[str, Any] = Depends(mock_config_data),
    subentries: list[ConfigSubentryData] = Depends(mock_subentries),
) -> MockConfigEntry:
    """Mock a wsdot config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data=config_data,
        subentries_data=subentries,
    )


@fixture
async def init_integration(
    hass: HomeAssistant = Depends(hass_fx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _travel_time: AsyncMock = Depends(mock_travel_time),
) -> MockConfigEntry:
    """Set up wsdot integration with subentries for testing."""
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    return config_entry


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock config entry setup."""
    with patch(
        "homeassistant.components.wsdot.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup
