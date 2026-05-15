"""Tryke fixtures for trafikverket_ferry tests."""

from datetime import datetime, timedelta
from unittest.mock import patch

from pytrafikverket.models import FerryStopModel
from tryke import Depends, fixture

from homeassistant.components.trafikverket_ferry.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from tests.common import MockConfigEntry
from tests.components.trafikverket_ferry import ENTRY_CONFIG
from tests.hass_fixtures import hass as hass_fixture

_FAKE_TRANSLATIONS = {
    "component.trafikverket_ferry.entity.sensor.departure_from.name": "Departure from",
    "component.trafikverket_ferry.entity.sensor.departure_to.name": "Departure to",
    "component.trafikverket_ferry.entity.sensor.departure_time.name": "Departure time",
    "component.trafikverket_ferry.entity.sensor.departure_modified.name": (
        "Departure modified"
    ),
    "component.trafikverket_ferry.entity.sensor.departure_time_next.name": (
        "Departure time next"
    ),
    "component.trafikverket_ferry.entity.sensor.departure_time_next_next.name": (
        "Departure time next after"
    ),
}


async def _fake_get_translations(
    hass_arg, language, category, integrations=None, config_flow=None
):
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(hass_arg, language, category, integration=None):
    return _FAKE_TRANSLATIONS


@fixture
def get_ferries() -> list[FerryStopModel]:
    """Construct FerryStop Mock."""
    depart1 = FerryStopModel(
        ferry_stop_id="13",
        ferry_stop_name="Harbor1lane",
        short_name="Harle",
        deleted=False,
        departure_time=datetime(
            dt_util.now().year + 1, 5, 1, 12, 0, tzinfo=dt_util.UTC
        ),
        other_information=[""],
        deviation_id="0",
        modified_time=datetime(dt_util.now().year, 5, 1, 12, 0, tzinfo=dt_util.UTC),
        from_harbor_name="Harbor 1",
        to_harbor_name="Harbor 2",
        type_name="Turnaround",
    )
    depart2 = FerryStopModel(
        ferry_stop_id="14",
        ferry_stop_name="Harbor1lane",
        short_name="Harle",
        deleted=False,
        departure_time=datetime(dt_util.now().year + 1, 5, 1, 12, 0, tzinfo=dt_util.UTC)
        + timedelta(minutes=15),
        other_information=[""],
        deviation_id="0",
        modified_time=datetime(dt_util.now().year, 5, 1, 12, 0, tzinfo=dt_util.UTC),
        from_harbor_name="Harbor 1",
        to_harbor_name="Harbor 2",
        type_name="Turnaround",
    )
    depart3 = FerryStopModel(
        ferry_stop_id="15",
        ferry_stop_name="Harbor1lane",
        short_name="Harle",
        deleted=False,
        departure_time=datetime(dt_util.now().year + 1, 5, 1, 12, 0, tzinfo=dt_util.UTC)
        + timedelta(minutes=30),
        other_information=[""],
        deviation_id="0",
        modified_time=datetime(dt_util.now().year, 5, 1, 12, 0, tzinfo=dt_util.UTC),
        from_harbor_name="Harbor 1",
        to_harbor_name="Harbor 2",
        type_name="Turnaround",
    )
    return [depart1, depart2, depart3]


@fixture
async def load_int(
    hass: HomeAssistant = Depends(hass_fixture),
    get_ferries: list[FerryStopModel] = Depends(get_ferries),
) -> MockConfigEntry:
    """Set up the Trafikverket Ferry integration in Home Assistant."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data=ENTRY_CONFIG,
        entry_id="1",
        unique_id="123",
    )

    config_entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.trafikverket_ferry.coordinator.TrafikverketFerry.async_get_next_ferry_stops",
            return_value=get_ferries,
        ),
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    return config_entry
