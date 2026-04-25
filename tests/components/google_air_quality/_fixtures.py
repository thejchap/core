"""Tryke fixtures for Google Air Quality tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, Mock, patch

from google_air_quality_api.model import AirQualityCurrentConditionsData
from tryke import Depends, fixture

from homeassistant.components.google_air_quality import CONF_REFERRER
from homeassistant.components.google_air_quality.const import DOMAIN
from homeassistant.config_entries import ConfigSubentryDataWithId
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE

from tests.common import MockConfigEntry, load_json_object_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.google_air_quality.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_subentries() -> list[ConfigSubentryDataWithId]:
    """Fixture for subentries."""
    return [
        ConfigSubentryDataWithId(
            data={CONF_LATITUDE: 10.1, CONF_LONGITUDE: 20.1},
            subentry_type="location",
            title="Home",
            subentry_id="home-subentry-id",
            unique_id=None,
        )
    ]


@fixture
def mock_config_entry(
    mock_subentries: list[ConfigSubentryDataWithId] = Depends(mock_subentries),
) -> MockConfigEntry:
    """Fixture for a config and a subentry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=DOMAIN,
        data={CONF_API_KEY: "test-api-key", CONF_REFERRER: None},
        entry_id="123456789",
        subentries_data=[*mock_subentries],
    )


@fixture
def mock_api() -> Generator[Mock]:
    """Set up fake Google Air Quality API responses from fixtures."""
    responses = load_json_object_fixture("air_quality_data.json", DOMAIN)
    with (
        patch(
            "homeassistant.components.google_air_quality.GoogleAirQualityApi",
            autospec=True,
        ) as mock_api,
        patch(
            "homeassistant.components.google_air_quality.config_flow.GoogleAirQualityApi",
            new=mock_api,
        ),
    ):
        api = mock_api.return_value
        api.async_get_current_conditions.return_value = (
            AirQualityCurrentConditionsData.from_dict(responses)
        )
        yield api
