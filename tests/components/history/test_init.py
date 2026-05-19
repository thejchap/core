"""The tests the History component."""

from __future__ import annotations

from datetime import datetime, timedelta
from http import HTTPStatus
import json
from typing import Any
from unittest.mock import sentinel

from freezegun import freeze_time
from tryke import Depends, expect, fixture, test

from homeassistant.components import history
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.components.recorder.models import process_timestamp
from homeassistant.const import EVENT_HOMEASSISTANT_FINAL_WRITE
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.json import JSONEncoder
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from ._fixtures import hass_history, recorder_mock

from tests.common import MockUser
from tests.components.recorder.common import (
    assert_dict_of_states_equal_without_context_and_last_changed,
    assert_multiple_states_equal_without_context,
    assert_multiple_states_equal_without_context_and_last_changed,
    assert_states_equal_without_context,
    async_wait_recording_done,
)
from tests.hass_fixtures import (
    ClientSessionGenerator,
    caplog as caplog_fixture,
    hass as hass_fixture,
    hass_client,
    hass_read_only_access_token,
    hass_read_only_user,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Tryke executor trigger for async fixtures with Depends."""
    return 0


def listeners_without_writes(listeners: dict[str, int]) -> dict[str, int]:
    """Return listeners without final write listeners since we are not testing for these."""
    return {
        key: value
        for key, value in listeners.items()
        if key != EVENT_HOMEASSISTANT_FINAL_WRITE
    }


async def async_record_states(
    hass: HomeAssistant,
) -> tuple[datetime, datetime, dict[str, list[State | None]]]:
    """Record some test states.

    We inject a bunch of state updates from media player, zone and
    thermostat.
    """
    mp = "media_player.test"
    mp2 = "media_player.test2"
    mp3 = "media_player.test3"
    therm = "thermostat.test"
    therm2 = "thermostat.test2"
    zone = "zone.home"
    script_c = "script.can_cancel_this_one"

    async def set_state(entity_id: str, state: Any, **kwargs: Any) -> State:
        """Set the state."""
        hass.states.async_set(entity_id, state, **kwargs)
        await async_wait_recording_done(hass)
        return hass.states.get(entity_id)

    zero = dt_util.utcnow()
    one = zero + timedelta(seconds=1)
    two = one + timedelta(seconds=1)
    three = two + timedelta(seconds=1)
    four = three + timedelta(seconds=1)

    states: dict[str, list[State | None]] = {
        therm: [],
        therm2: [],
        mp: [],
        mp2: [],
        mp3: [],
        script_c: [],
    }
    with freeze_time(one) as freezer:
        states[mp].append(
            await set_state(mp, "idle", attributes={"media_title": str(sentinel.mt1)})
        )
        states[mp2].append(
            await set_state(
                mp2, "YouTube", attributes={"media_title": str(sentinel.mt2)}
            )
        )
        states[mp3].append(
            await set_state(mp3, "idle", attributes={"media_title": str(sentinel.mt1)})
        )
        states[therm].append(
            await set_state(therm, 20, attributes={"current_temperature": 19.5})
        )

        freezer.move_to(one + timedelta(microseconds=1))
        states[mp].append(
            await set_state(
                mp, "YouTube", attributes={"media_title": str(sentinel.mt2)}
            )
        )

        freezer.move_to(two)
        # This state will be skipped only different in time
        await set_state(mp, "YouTube", attributes={"media_title": str(sentinel.mt3)})
        # This state will be skipped because domain is excluded
        await set_state(zone, "zoning")
        states[script_c].append(
            await set_state(script_c, "off", attributes={"can_cancel": True})
        )
        states[therm].append(
            await set_state(therm, 21, attributes={"current_temperature": 19.8})
        )
        states[therm2].append(
            await set_state(therm2, 20, attributes={"current_temperature": 19})
        )

        freezer.move_to(three)
        states[mp].append(
            await set_state(
                mp, "Netflix", attributes={"media_title": str(sentinel.mt4)}
            )
        )
        states[mp3].append(
            await set_state(
                mp3, "Netflix", attributes={"media_title": str(sentinel.mt3)}
            )
        )
        # Attributes changed even though state is the same
        states[therm].append(
            await set_state(therm, 21, attributes={"current_temperature": 20})
        )

    return zero, four, states


@test
async def setup(
    _trigger: int = Depends(_trigger_executor),
    _hass_history: None = Depends(hass_history),
) -> None:
    """Test setup method of history."""
    # Verification occurs in the fixture


@test
async def get_significant_states_test(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _hass_history: None = Depends(hass_history),
) -> None:
    """Test that only significant states are returned."""
    zero, four, states = await async_record_states(hass)
    hist = get_significant_states(hass, zero, four, entity_ids=list(states))
    assert_dict_of_states_equal_without_context_and_last_changed(states, hist)


@test
async def get_significant_states_minimal_response(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _hass_history: None = Depends(hass_history),
) -> None:
    """Test that only significant states are returned with minimal responses."""
    zero, four, states = await async_record_states(hass)
    hist = get_significant_states(
        hass, zero, four, minimal_response=True, entity_ids=list(states)
    )
    entites_with_reducable_states = [
        "media_player.test",
        "media_player.test3",
    ]

    for entity_id in entites_with_reducable_states:
        entity_states = states[entity_id]
        for state_idx in range(1, len(entity_states)):
            input_state = entity_states[state_idx]
            orig_last_changed = json.dumps(
                process_timestamp(input_state.last_changed),
                cls=JSONEncoder,
            ).replace('"', "")
            orig_state = input_state.state
            entity_states[state_idx] = {
                "last_changed": orig_last_changed,
                "state": orig_state,
            }
    expect(len(hist)).to_equal(len(states))
    assert_states_equal_without_context(
        states["media_player.test"][0], hist["media_player.test"][0]
    )
    expect(states["media_player.test"][1]).to_equal(hist["media_player.test"][1])
    expect(states["media_player.test"][2]).to_equal(hist["media_player.test"][2])

    assert_multiple_states_equal_without_context(
        states["media_player.test2"], hist["media_player.test2"]
    )
    assert_states_equal_without_context(
        states["media_player.test3"][0], hist["media_player.test3"][0]
    )
    expect(states["media_player.test3"][1]).to_equal(hist["media_player.test3"][1])

    assert_multiple_states_equal_without_context(
        states["script.can_cancel_this_one"], hist["script.can_cancel_this_one"]
    )
    assert_multiple_states_equal_without_context_and_last_changed(
        states["thermostat.test"], hist["thermostat.test"]
    )
    assert_multiple_states_equal_without_context_and_last_changed(
        states["thermostat.test2"], hist["thermostat.test2"]
    )


@test
async def get_significant_states_with_initial(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _hass_history: None = Depends(hass_history),
) -> None:
    """Test that only significant states are returned with include_start_time_state."""
    zero, four, states = await async_record_states(hass)
    one_and_half = zero + timedelta(seconds=1.5)
    for entity_id in states:
        if entity_id == "media_player.test":
            states[entity_id] = states[entity_id][1:]
        for state in states[entity_id]:
            if state.last_updated < one_and_half:
                state.last_updated = one_and_half
                state.last_changed = one_and_half

    hist = get_significant_states(
        hass, one_and_half, four, include_start_time_state=True, entity_ids=list(states)
    )
    assert_dict_of_states_equal_without_context_and_last_changed(states, hist)


@test
async def get_significant_states_without_initial(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _hass_history: None = Depends(hass_history),
) -> None:
    """Test that only significant states are returned without start time state."""
    zero, four, states = await async_record_states(hass)
    one = zero + timedelta(seconds=1)
    one_with_microsecond = zero + timedelta(seconds=1, microseconds=1)
    one_and_half = zero + timedelta(seconds=1.5)
    for entity_id in states:
        states[entity_id] = [
            s
            for s in states[entity_id]
            if s.last_changed not in (one, one_with_microsecond)
        ]
    del states["media_player.test2"]

    hist = get_significant_states(
        hass,
        one_and_half,
        four,
        include_start_time_state=False,
        entity_ids=list(states),
    )
    assert_dict_of_states_equal_without_context_and_last_changed(states, hist)


@test
async def get_significant_states_entity_id(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _hass_history: None = Depends(hass_history),
) -> None:
    """Test that only significant states are returned for one entity."""
    zero, four, states = await async_record_states(hass)
    del states["media_player.test2"]
    del states["media_player.test3"]
    del states["thermostat.test"]
    del states["thermostat.test2"]
    del states["script.can_cancel_this_one"]

    hist = get_significant_states(hass, zero, four, ["media_player.test"])
    assert_dict_of_states_equal_without_context_and_last_changed(states, hist)


@test
async def get_significant_states_multiple_entity_ids(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _hass_history: None = Depends(hass_history),
) -> None:
    """Test that only significant states are returned for multiple entities."""
    zero, four, states = await async_record_states(hass)
    del states["media_player.test2"]
    del states["media_player.test3"]
    del states["thermostat.test2"]
    del states["script.can_cancel_this_one"]

    hist = get_significant_states(
        hass,
        zero,
        four,
        ["media_player.test", "thermostat.test"],
    )
    assert_dict_of_states_equal_without_context_and_last_changed(states, hist)


@test
async def get_significant_states_are_ordered(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _hass_history: None = Depends(hass_history),
) -> None:
    """Test order of results from get_significant_states."""
    zero, four, _states = await async_record_states(hass)
    entity_ids = ["media_player.test", "media_player.test2"]
    hist = get_significant_states(hass, zero, four, entity_ids)
    expect(list(hist.keys())).to_equal(entity_ids)
    entity_ids = ["media_player.test2", "media_player.test"]
    hist = get_significant_states(hass, zero, four, entity_ids)
    expect(list(hist.keys())).to_equal(entity_ids)


@test
async def get_significant_states_only(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _hass_history: None = Depends(hass_history),
) -> None:
    """Test significant states when significant_states_only is set."""
    entity_id = "sensor.test"

    async def set_state(state: Any, **kwargs: Any) -> State:
        """Set the state."""
        hass.states.async_set(entity_id, state, **kwargs)
        await async_wait_recording_done(hass)
        return hass.states.get(entity_id)

    start = dt_util.utcnow() - timedelta(minutes=4)
    points = [start + timedelta(minutes=i) for i in range(1, 4)]

    states = []
    with freeze_time(start) as freezer:
        await set_state("123", attributes={"attribute": 10.64})

        freezer.move_to(points[0])
        states.append(await set_state("123", attributes={"attribute": 21.42}))

        freezer.move_to(points[1])
        states.append(await set_state("32", attributes={"attribute": 21.42}))

        freezer.move_to(points[2])
        states.append(await set_state("412", attributes={"attribute": 54.23}))

    hist = get_significant_states(
        hass,
        start,
        significant_changes_only=True,
        entity_ids=list({state.entity_id for state in states}),
    )

    expect(len(hist[entity_id])).to_equal(2)
    expect(
        any(state.last_updated == states[0].last_updated for state in hist[entity_id])
    ).to_be(False)
    expect(
        any(state.last_updated == states[1].last_updated for state in hist[entity_id])
    ).to_be(True)
    expect(
        any(state.last_updated == states[2].last_updated for state in hist[entity_id])
    ).to_be(True)

    hist = get_significant_states(
        hass,
        start,
        significant_changes_only=False,
        entity_ids=list({state.entity_id for state in states}),
    )

    expect(len(hist[entity_id])).to_equal(3)
    assert_multiple_states_equal_without_context_and_last_changed(
        states, hist[entity_id]
    )


@test
async def fetch_period_api(
    _trigger: int = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the fetch period view for history."""
    await async_setup_component(hass, "history", {})
    client = await hass_client()
    response = await client.get(
        f"/api/history/period/{dt_util.utcnow().isoformat()}?filter_entity_id=sensor.power"
    )
    expect(response.status).to_equal(HTTPStatus.OK)


@test
async def fetch_period_api_with_use_include_order(
    _trigger: int = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
    caplog=Depends(caplog_fixture),
) -> None:
    """Test the fetch period view for history with include order."""
    await async_setup_component(
        hass, "history", {history.DOMAIN: {history.CONF_ORDER: True}}
    )
    client = await hass_client()
    response = await client.get(
        f"/api/history/period/{dt_util.utcnow().isoformat()}?filter_entity_id=sensor.power"
    )
    expect(response.status).to_equal(HTTPStatus.OK)

    expect("The 'use_include_order' option is deprecated" in caplog.text).to_be(True)


@test
async def fetch_period_api_with_minimal_response(
    _trigger: int = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the fetch period view for history with minimal_response."""
    now = dt_util.utcnow()
    await async_setup_component(hass, "history", {})

    hass.states.async_set("sensor.power", 0, {"attr": "any"})
    await async_wait_recording_done(hass)
    hass.states.async_set("sensor.power", 50, {"attr": "any"})
    await async_wait_recording_done(hass)
    hass.states.async_set("sensor.power", 23, {"attr": "any"})
    last_changed = hass.states.get("sensor.power").last_changed
    await async_wait_recording_done(hass)
    hass.states.async_set("sensor.power", 23, {"attr": "any"})
    await async_wait_recording_done(hass)
    client = await hass_client()
    response = await client.get(
        f"/api/history/period/{now.isoformat()}?filter_entity_id=sensor.power&minimal_response&no_attributes"
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    response_json = await response.json()
    expect(len(response_json[0])).to_equal(3)
    state_list = response_json[0]

    expect(state_list[0]["entity_id"]).to_equal("sensor.power")
    expect(state_list[0]["attributes"]).to_equal({})
    expect(state_list[0]["state"]).to_equal("0")

    expect("attributes" not in state_list[1]).to_be(True)
    expect("entity_id" not in state_list[1]).to_be(True)
    expect(state_list[1]["state"]).to_equal("50")

    expect("attributes" not in state_list[2]).to_be(True)
    expect("entity_id" not in state_list[2]).to_be(True)
    expect(state_list[2]["state"]).to_equal("23")
    expect(state_list[2]["last_changed"]).to_equal(
        json.dumps(
            process_timestamp(last_changed),
            cls=JSONEncoder,
        ).replace('"', "")
    )


@test
async def fetch_period_api_with_no_timestamp(
    _trigger: int = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the fetch period view for history with no timestamp."""
    await async_setup_component(hass, "history", {})
    client = await hass_client()
    response = await client.get("/api/history/period?filter_entity_id=sensor.power")
    expect(response.status).to_equal(HTTPStatus.OK)


@test
async def fetch_period_api_with_include_order(
    _trigger: int = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
    caplog=Depends(caplog_fixture),
) -> None:
    """Test the fetch period view for history with include order."""
    await async_setup_component(
        hass,
        "history",
        {
            "history": {
                "use_include_order": True,
                "include": {"entities": ["light.kitchen"]},
            }
        },
    )
    client = await hass_client()
    response = await client.get(
        f"/api/history/period/{dt_util.utcnow().isoformat()}",
        params={"filter_entity_id": "non.existing,something.else"},
    )
    expect(response.status).to_equal(HTTPStatus.OK)

    expect("The 'use_include_order' option is deprecated" in caplog.text).to_be(True)
    expect("The 'include' option is deprecated" in caplog.text).to_be(True)


@test
async def entity_ids_limit_via_api(
    _trigger: int = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test limiting history to entity_ids."""
    await async_setup_component(
        hass,
        "history",
        {"history": {}},
    )
    hass.states.async_set("light.kitchen", "on")
    hass.states.async_set("light.cow", "on")
    hass.states.async_set("light.nomatch", "on")

    await async_wait_recording_done(hass)

    client = await hass_client()
    response = await client.get(
        f"/api/history/period/{dt_util.utcnow().isoformat()}?filter_entity_id=light.kitchen,light.cow",
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    response_json = await response.json()
    expect(len(response_json)).to_equal(2)
    expect(response_json[0][0]["entity_id"]).to_equal("light.kitchen")
    expect(response_json[1][0]["entity_id"]).to_equal("light.cow")


@test
async def entity_ids_limit_via_api_with_skip_initial_state(
    _trigger: int = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test limiting history to entity_ids with skip_initial_state."""
    await async_setup_component(
        hass,
        "history",
        {"history": {}},
    )
    hass.states.async_set("light.kitchen", "on")
    hass.states.async_set("light.cow", "on")
    hass.states.async_set("light.nomatch", "on")

    await async_wait_recording_done(hass)

    client = await hass_client()
    response = await client.get(
        f"/api/history/period/{dt_util.utcnow().isoformat()}?filter_entity_id=light.kitchen,light.cow&skip_initial_state",
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    response_json = await response.json()
    expect(len(response_json)).to_equal(0)

    when = dt_util.utcnow() - timedelta(minutes=1)
    response = await client.get(
        f"/api/history/period/{when.isoformat()}?filter_entity_id=light.kitchen,light.cow&skip_initial_state",
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    response_json = await response.json()
    expect(len(response_json)).to_equal(2)
    expect(response_json[0][0]["entity_id"]).to_equal("light.kitchen")
    expect(response_json[1][0]["entity_id"]).to_equal("light.cow")


@test
async def fetch_period_api_before_history_started(
    _trigger: int = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the fetch period view for history for the far past."""
    await async_setup_component(
        hass,
        "history",
        {},
    )
    await async_wait_recording_done(hass)
    far_past = dt_util.utcnow() - timedelta(days=365)

    client = await hass_client()
    response = await client.get(
        f"/api/history/period/{far_past.isoformat()}?filter_entity_id=light.kitchen",
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    response_json = await response.json()
    expect(response_json).to_equal([])


@test
async def fetch_period_api_far_future(
    _trigger: int = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the fetch period view for history for the far future."""
    await async_setup_component(
        hass,
        "history",
        {},
    )
    await async_wait_recording_done(hass)
    far_future = dt_util.utcnow() + timedelta(days=365)

    client = await hass_client()
    response = await client.get(
        f"/api/history/period/{far_future.isoformat()}?filter_entity_id=light.kitchen",
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    response_json = await response.json()
    expect(response_json).to_equal([])


@test
async def fetch_period_api_with_invalid_datetime(
    _trigger: int = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the fetch period view for history with an invalid date time."""
    await async_setup_component(
        hass,
        "history",
        {},
    )
    await async_wait_recording_done(hass)
    client = await hass_client()
    response = await client.get(
        "/api/history/period/INVALID?filter_entity_id=light.kitchen",
    )
    expect(response.status).to_equal(HTTPStatus.BAD_REQUEST)
    response_json = await response.json()
    expect(response_json).to_equal({"message": "Invalid datetime"})


@test
async def fetch_period_api_invalid_end_time(
    _trigger: int = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the fetch period view for history with an invalid end time."""
    await async_setup_component(
        hass,
        "history",
        {},
    )
    await async_wait_recording_done(hass)
    far_past = dt_util.utcnow() - timedelta(days=365)

    client = await hass_client()
    response = await client.get(
        f"/api/history/period/{far_past.isoformat()}",
        params={"filter_entity_id": "light.kitchen", "end_time": "INVALID"},
    )
    expect(response.status).to_equal(HTTPStatus.BAD_REQUEST)
    response_json = await response.json()
    expect(response_json).to_equal({"message": "Invalid end_time"})


@test
async def entity_ids_limit_via_api_with_end_time(
    _trigger: int = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test limiting history to entity_ids with end_time."""
    await async_setup_component(
        hass,
        "history",
        {"history": {}},
    )
    start = dt_util.utcnow()
    hass.states.async_set("light.kitchen", "on")
    hass.states.async_set("light.cow", "on")
    hass.states.async_set("light.nomatch", "on")

    await async_wait_recording_done(hass)

    end_time = start + timedelta(minutes=1)
    future_second = dt_util.utcnow() + timedelta(seconds=1)

    client = await hass_client()
    response = await client.get(
        f"/api/history/period/{future_second.isoformat()}",
        params={
            "filter_entity_id": "light.kitchen,light.cow",
            "end_time": end_time.isoformat(),
        },
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    response_json = await response.json()
    expect(len(response_json)).to_equal(0)

    when = start - timedelta(minutes=1)
    response = await client.get(
        f"/api/history/period/{when.isoformat()}",
        params={
            "filter_entity_id": "light.kitchen,light.cow",
            "end_time": end_time.isoformat(),
        },
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    response_json = await response.json()
    expect(len(response_json)).to_equal(2)
    expect(response_json[0][0]["entity_id"]).to_equal("light.kitchen")
    expect(response_json[1][0]["entity_id"]).to_equal("light.cow")


@test
async def fetch_period_api_with_no_entity_ids(
    _trigger: int = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the fetch period view for history with no entity ids."""
    await async_setup_component(hass, "history", {})
    await async_wait_recording_done(hass)

    yesterday = dt_util.utcnow() - timedelta(days=1)

    client = await hass_client()
    response = await client.get(f"/api/history/period/{yesterday.isoformat()}")
    expect(response.status).to_equal(HTTPStatus.BAD_REQUEST)
    response_json = await response.json()
    expect(response_json).to_equal({"message": "filter_entity_id is missing"})


@test.cases(
    test.case(
        "valid",
        filter_entity_id="light.kitchen,light.cow",
        status_code=200,
        response_contains1="light.kitchen",
        response_contains2="light.cow",
    ),
    test.case(
        "trailing_amp",
        filter_entity_id="light.kitchen,light.cow&",
        status_code=400,
        response_contains1="message",
        response_contains2="Invalid filter_entity_id",
    ),
    test.case(
        "hyphen_in_entity",
        filter_entity_id="light.kitchen,li-ght.cow",
        status_code=400,
        response_contains1="message",
        response_contains2="Invalid filter_entity_id",
    ),
    test.case(
        "bang_in_entity",
        filter_entity_id="light.kit!chen",
        status_code=400,
        response_contains1="message",
        response_contains2="Invalid filter_entity_id",
    ),
    test.case(
        "plus_in_entity",
        filter_entity_id="lig+ht.kitchen,light.cow",
        status_code=400,
        response_contains1="message",
        response_contains2="Invalid filter_entity_id",
    ),
    test.case(
        "missing_comma",
        filter_entity_id="light.kitchenlight.cow",
        status_code=400,
        response_contains1="message",
        response_contains2="Invalid filter_entity_id",
    ),
    test.case(
        "no_domain",
        filter_entity_id="cow",
        status_code=400,
        response_contains1="message",
        response_contains2="Invalid filter_entity_id",
    ),
)
async def history_with_invalid_entity_ids(
    filter_entity_id: str,
    status_code: int,
    response_contains1: str,
    response_contains2: str,
    _trigger: int = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test sending valid and invalid entity_ids to the API."""
    await async_setup_component(
        hass,
        "history",
        {"history": {}},
    )
    hass.states.async_set("light.kitchen", "on")
    hass.states.async_set("light.cow", "on")

    await async_wait_recording_done(hass)
    now = dt_util.utcnow().isoformat()
    client = await hass_client()

    response = await client.get(
        f"/api/history/period/{now}",
        params={"filter_entity_id": filter_entity_id},
    )
    expect(response.status).to_equal(status_code)
    response_json = await response.json()
    expect(response_contains1 in str(response_json)).to_be(True)
    expect(response_contains2 in str(response_json)).to_be(True)


@test
async def fetch_period_api_filters_unauthorized_entities(
    _trigger: int = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    read_only_user: MockUser = Depends(hass_read_only_user),
    read_only_token: str = Depends(hass_read_only_access_token),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test history is filtered by per-entity read permissions for non-admins."""
    expect(read_only_user.is_admin).to_be(False)
    read_only_user.mock_policy(
        {"entities": {"entity_ids": {"light.kitchen": True}}}
    )
    await async_setup_component(hass, "history", {})

    hass.states.async_set("light.kitchen", "on")
    hass.states.async_set("light.cow", "on")
    await async_wait_recording_done(hass)

    client = await hass_client(read_only_token)

    now = dt_util.utcnow().isoformat()
    response = await client.get(
        f"/api/history/period/{now}",
        params={"filter_entity_id": "light.kitchen,light.cow"},
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    response_json = await response.json()
    expect(
        all(
            state["entity_id"] == "light.kitchen"
            for entity_states in response_json
            for state in entity_states
        )
    ).to_be(True)

    response = await client.get(
        f"/api/history/period/{now}",
        params={"filter_entity_id": "light.cow"},
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    expect(await response.json()).to_equal([])
