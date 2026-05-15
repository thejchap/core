"""The tests for the Queensland Bushfire Alert Feed platform."""

import datetime
from unittest.mock import MagicMock, call, patch

from freezegun.api import FrozenDateTimeFactory
from georss_qld_bushfire_alert_client import QldBushfireAlertFeed
from tryke import Depends, expect, fixture, test

from homeassistant.components import geo_location
from homeassistant.components.geo_location import ATTR_SOURCE
from homeassistant.components.qld_bushfire.geo_location import (
    ATTR_CATEGORY,
    ATTR_EXTERNAL_ID,
    ATTR_PUBLICATION_DATE,
    ATTR_STATUS,
    ATTR_UPDATED_DATE,
    SCAN_INTERVAL,
)
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
    EVENT_HOMEASSISTANT_START,
    UnitOfLength,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import assert_setup_component, async_fire_time_changed
from tests.hass_fixtures import (
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)

CONFIG = {geo_location.DOMAIN: [{"platform": "qld_bushfire", CONF_RADIUS: 200}]}

CONFIG_WITH_CUSTOM_LOCATION = {
    geo_location.DOMAIN: [
        {
            "platform": "qld_bushfire",
            CONF_RADIUS: 200,
            CONF_LATITUDE: 40.4,
            CONF_LONGITUDE: -3.7,
        }
    ]
}


def _generate_mock_feed_entry(
    external_id,
    title,
    distance_to_home,
    coordinates,
    category=None,
    attribution=None,
    published=None,
    updated=None,
    status=None,
):
    """Construct a mock feed entry for testing purposes."""
    feed_entry = MagicMock()
    feed_entry.external_id = external_id
    feed_entry.title = title
    feed_entry.distance_to_home = distance_to_home
    feed_entry.coordinates = coordinates
    feed_entry.category = category
    feed_entry.attribution = attribution
    feed_entry.published = published
    feed_entry.updated = updated
    feed_entry.status = status
    return feed_entry


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test the general setup of the platform."""
    mock_entry_1 = _generate_mock_feed_entry(
        "1234",
        "Title 1",
        15.5,
        (38.0, -3.0),
        category="Category 1",
        attribution="Attribution 1",
        published=datetime.datetime(2018, 9, 22, 8, 0, tzinfo=datetime.UTC),
        updated=datetime.datetime(2018, 9, 22, 8, 10, tzinfo=datetime.UTC),
        status="Status 1",
    )
    mock_entry_2 = _generate_mock_feed_entry("2345", "Title 2", 20.5, (38.1, -3.1))
    mock_entry_3 = _generate_mock_feed_entry("3456", "Title 3", 25.5, (38.2, -3.2))
    mock_entry_4 = _generate_mock_feed_entry("4567", "Title 4", 12.5, (38.3, -3.3))

    utcnow = dt_util.utcnow()
    freezer.move_to(utcnow)

    with patch("georss_client.feed.GeoRssFeed.update") as mock_feed_update:
        mock_feed_update.return_value = (
            "OK",
            [mock_entry_1, mock_entry_2, mock_entry_3],
        )
        with assert_setup_component(1, geo_location.DOMAIN):
            expect(
                bool(await async_setup_component(hass, geo_location.DOMAIN, CONFIG))
            ).to_be(True)
            await hass.async_block_till_done()
            hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
            await hass.async_block_till_done()

            all_states = hass.states.async_all()
            expect(len(all_states)).to_equal(3)

            state = hass.states.get("geo_location.title_1")
            expect(state is not None).to_be(True)
            expect(state.name).to_equal("Title 1")
            expect(state.attributes).to_equal(
                {
                    ATTR_EXTERNAL_ID: "1234",
                    ATTR_LATITUDE: 38.0,
                    ATTR_LONGITUDE: -3.0,
                    ATTR_FRIENDLY_NAME: "Title 1",
                    ATTR_CATEGORY: "Category 1",
                    ATTR_ATTRIBUTION: "Attribution 1",
                    ATTR_PUBLICATION_DATE: datetime.datetime(
                        2018, 9, 22, 8, 0, tzinfo=datetime.UTC
                    ),
                    ATTR_UPDATED_DATE: datetime.datetime(
                        2018, 9, 22, 8, 10, tzinfo=datetime.UTC
                    ),
                    ATTR_STATUS: "Status 1",
                    ATTR_UNIT_OF_MEASUREMENT: UnitOfLength.KILOMETERS,
                    ATTR_SOURCE: "qld_bushfire",
                    ATTR_ICON: "mdi:fire",
                }
            )
            expect(float(state.state)).to_equal(15.5)

            state = hass.states.get("geo_location.title_2")
            expect(state is not None).to_be(True)
            expect(state.name).to_equal("Title 2")
            expect(state.attributes).to_equal(
                {
                    ATTR_EXTERNAL_ID: "2345",
                    ATTR_LATITUDE: 38.1,
                    ATTR_LONGITUDE: -3.1,
                    ATTR_FRIENDLY_NAME: "Title 2",
                    ATTR_UNIT_OF_MEASUREMENT: UnitOfLength.KILOMETERS,
                    ATTR_SOURCE: "qld_bushfire",
                    ATTR_ICON: "mdi:fire",
                }
            )
            expect(float(state.state)).to_equal(20.5)

            state = hass.states.get("geo_location.title_3")
            expect(state is not None).to_be(True)
            expect(state.name).to_equal("Title 3")
            expect(state.attributes).to_equal(
                {
                    ATTR_EXTERNAL_ID: "3456",
                    ATTR_LATITUDE: 38.2,
                    ATTR_LONGITUDE: -3.2,
                    ATTR_FRIENDLY_NAME: "Title 3",
                    ATTR_UNIT_OF_MEASUREMENT: UnitOfLength.KILOMETERS,
                    ATTR_SOURCE: "qld_bushfire",
                    ATTR_ICON: "mdi:fire",
                }
            )
            expect(float(state.state)).to_equal(25.5)

            mock_feed_update.return_value = (
                "OK",
                [mock_entry_1, mock_entry_4, mock_entry_3],
            )
            async_fire_time_changed(hass, utcnow + SCAN_INTERVAL)
            await hass.async_block_till_done(wait_background_tasks=True)

            all_states = hass.states.async_all()
            expect(len(all_states)).to_equal(3)

            mock_feed_update.return_value = "OK_NO_DATA", None
            async_fire_time_changed(hass, utcnow + 2 * SCAN_INTERVAL)
            await hass.async_block_till_done(wait_background_tasks=True)

            all_states = hass.states.async_all()
            expect(len(all_states)).to_equal(3)

            mock_feed_update.return_value = "ERROR", None
            async_fire_time_changed(hass, utcnow + 3 * SCAN_INTERVAL)
            await hass.async_block_till_done(wait_background_tasks=True)

            all_states = hass.states.async_all()
            expect(len(all_states)).to_equal(0)


@test
async def setup_with_custom_location(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the setup with a custom location."""
    mock_entry_1 = _generate_mock_feed_entry(
        "1234", "Title 1", 20.5, (38.1, -3.1), category="Category 1"
    )

    with (
        patch(
            "georss_qld_bushfire_alert_client.feed_manager.QldBushfireAlertFeed",
            wraps=QldBushfireAlertFeed,
        ) as mock_feed,
        patch("georss_client.feed.GeoRssFeed.update") as mock_feed_update,
    ):
        mock_feed_update.return_value = "OK", [mock_entry_1]

        with assert_setup_component(1, geo_location.DOMAIN):
            expect(
                bool(
                    await async_setup_component(
                        hass, geo_location.DOMAIN, CONFIG_WITH_CUSTOM_LOCATION
                    )
                )
            ).to_be(True)
            await hass.async_block_till_done()

            hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
            await hass.async_block_till_done()

            all_states = hass.states.async_all()
            expect(len(all_states)).to_equal(1)

            expect(mock_feed.call_args).to_equal(
                call((40.4, -3.7), filter_categories=[], filter_radius=200.0)
            )
