"""The test for the geo rss events sensor platform."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.components import sensor
from homeassistant.components.geo_rss_events import sensor as geo_rss_events
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    ATTR_UNIT_OF_MEASUREMENT,
    EVENT_HOMEASSISTANT_START,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import assert_setup_component, async_fire_time_changed
from tests.hass_fixtures import freezer, hass as hass_fixture, mock_network

URL = "http://geo.rss.local/geo_rss_events.xml"
VALID_CONFIG_WITH_CATEGORIES = {
    sensor.DOMAIN: [
        {
            "platform": "geo_rss_events",
            geo_rss_events.CONF_URL: URL,
            geo_rss_events.CONF_CATEGORIES: ["Category 1"],
        }
    ]
}
VALID_CONFIG = {
    sensor.DOMAIN: [{"platform": "geo_rss_events", geo_rss_events.CONF_URL: URL}]
}


@fixture
def mock_feed() -> Generator[MagicMock]:
    """Mock for homeassistant.components.geo_rss_events.sensor.GenericFeed."""
    with patch(
        "homeassistant.components.geo_rss_events.sensor.GenericFeed"
    ) as feed:
        yield feed


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


def _generate_mock_feed_entry(
    external_id, title, distance_to_home, coordinates, category
):
    """Construct a mock feed entry for testing purposes."""
    feed_entry = MagicMock()
    feed_entry.external_id = external_id
    feed_entry.title = title
    feed_entry.distance_to_home = distance_to_home
    feed_entry.coordinates = coordinates
    feed_entry.category = category
    return feed_entry


@test
async def setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer_fx: FrozenDateTimeFactory = Depends(freezer),
    feed: MagicMock = Depends(mock_feed),
) -> None:
    """Test the general setup of the platform."""
    mock_entry_1 = _generate_mock_feed_entry(
        "1234", "Title 1", 15.5, (-31.0, 150.0), "Category 1"
    )
    mock_entry_2 = _generate_mock_feed_entry(
        "2345", "Title 2", 20.5, (-31.1, 150.1), "Category 1"
    )
    feed.return_value.update.return_value = "OK", [mock_entry_1, mock_entry_2]

    utcnow = dt_util.utcnow()
    freezer_fx.move_to(utcnow)
    with assert_setup_component(1, sensor.DOMAIN):
        expect(await async_setup_component(hass, sensor.DOMAIN, VALID_CONFIG)).to_be(
            True
        )
        hass.bus.fire(EVENT_HOMEASSISTANT_START)
        await hass.async_block_till_done()

        all_states = hass.states.async_all()
        expect(len(all_states)).to_equal(1)

        state = hass.states.get("sensor.event_service_any")
        expect(state is not None).to_be(True)
        expect(state.name).to_equal("Event Service Any")
        expect(int(state.state)).to_equal(2)
        expect(state.attributes).to_equal(
            {
                ATTR_FRIENDLY_NAME: "Event Service Any",
                ATTR_UNIT_OF_MEASUREMENT: "Events",
                ATTR_ICON: "mdi:alert",
                "Title 1": "16km",
                "Title 2": "20km",
            }
        )

        # Simulate an update - empty data, but successful update,
        # so no changes to entities.
        feed.return_value.update.return_value = "OK_NO_DATA", None
        async_fire_time_changed(hass, utcnow + geo_rss_events.SCAN_INTERVAL)
        await hass.async_block_till_done(wait_background_tasks=True)

        all_states = hass.states.async_all()
        expect(len(all_states)).to_equal(1)
        state = hass.states.get("sensor.event_service_any")
        expect(int(state.state)).to_equal(2)

        # Simulate an update - empty data, removes all entities
        feed.return_value.update.return_value = "ERROR", None
        async_fire_time_changed(hass, utcnow + 2 * geo_rss_events.SCAN_INTERVAL)
        await hass.async_block_till_done(wait_background_tasks=True)

        all_states = hass.states.async_all()
        expect(len(all_states)).to_equal(1)
        state = hass.states.get("sensor.event_service_any")
        expect(int(state.state)).to_equal(0)
        expect(state.attributes).to_equal(
            {
                ATTR_FRIENDLY_NAME: "Event Service Any",
                ATTR_UNIT_OF_MEASUREMENT: "Events",
                ATTR_ICON: "mdi:alert",
            }
        )


@test
async def setup_with_categories(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    feed: MagicMock = Depends(mock_feed),
) -> None:
    """Test the general setup of the platform."""
    mock_entry_1 = _generate_mock_feed_entry(
        "1234", "Title 1", 15.5, (-31.0, 150.0), "Category 1"
    )
    mock_entry_2 = _generate_mock_feed_entry(
        "2345", "Title 2", 20.5, (-31.1, 150.1), "Category 1"
    )
    feed.return_value.update.return_value = "OK", [mock_entry_1, mock_entry_2]

    with assert_setup_component(1, sensor.DOMAIN):
        expect(
            await async_setup_component(
                hass, sensor.DOMAIN, VALID_CONFIG_WITH_CATEGORIES
            )
        ).to_be(True)
        hass.bus.fire(EVENT_HOMEASSISTANT_START)
        await hass.async_block_till_done()

        all_states = hass.states.async_all()
        expect(len(all_states)).to_equal(1)

        state = hass.states.get("sensor.event_service_category_1")
        expect(state is not None).to_be(True)
        expect(state.name).to_equal("Event Service Category 1")
        expect(int(state.state)).to_equal(2)
        expect(state.attributes).to_equal(
            {
                ATTR_FRIENDLY_NAME: "Event Service Category 1",
                ATTR_UNIT_OF_MEASUREMENT: "Events",
                ATTR_ICON: "mdi:alert",
                "Title 1": "16km",
                "Title 2": "20km",
            }
        )
