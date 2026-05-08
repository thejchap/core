"""Test Deluge coordinator.py methods."""

from tryke import expect, test

from homeassistant.components.deluge.const import DelugeSensorType
from homeassistant.components.deluge.coordinator import count_states

from . import GET_TORRENT_STATES_RESPONSE


@test
def get_count() -> None:
    """Tests count_states()."""

    states = count_states(GET_TORRENT_STATES_RESPONSE)

    expect(states[DelugeSensorType.DOWNLOADING_COUNT_SENSOR.value]).to_equal(1)
    expect(states[DelugeSensorType.SEEDING_COUNT_SENSOR.value]).to_equal(2)
