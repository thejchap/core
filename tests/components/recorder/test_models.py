"""The tests for the Recorder component."""

from datetime import datetime, timedelta
from unittest.mock import PropertyMock

from tryke import Depends, expect, fixture, test

from homeassistant import core as ha
from homeassistant.components.recorder.const import SupportedDialect
from homeassistant.components.recorder.db_schema import (
    EventData,
    Events,
    StateAttributes,
    States,
)
from homeassistant.components.recorder.models import (
    LazyState,
    process_timestamp,
    process_timestamp_to_utc_isoformat,
)
from homeassistant.const import EVENT_STATE_CHANGED
from homeassistant.exceptions import InvalidEntityFormatError
from homeassistant.util import dt as dt_util
from homeassistant.util.json import JSON_DECODE_EXCEPTIONS, json_loads

from tests.hass_fixtures import caplog as caplog_fx

from .common import (
    db_event_to_native,
    db_state_attributes_to_native,
    db_state_to_native,
)


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
def from_event_to_db_event() -> None:
    """Test converting event to db event."""
    event = ha.Event(
        "test_event",
        {"some_data": 15},
        context=ha.Context(
            id="01EYQZJXZ5Z1Z1Z1Z1Z1Z1Z1Z1",
            parent_id="01EYQZJXZ5Z1Z1Z1Z1Z1Z1Z1Z1",
            user_id="12345678901234567890123456789012",
        ),
    )
    db_event = Events.from_event(event)
    dialect = SupportedDialect.MYSQL
    db_event.event_data = EventData.shared_data_bytes_from_event(event, dialect)
    db_event.event_type = event.event_type
    expect(event.as_dict()).to_equal(db_event_to_native(db_event).as_dict())


@test
def from_event_to_db_event_with_null() -> None:
    """Test converting event to EventData with a null with PostgreSQL."""
    event = ha.Event(
        "test_event",
        {"some_data": "withnull\0terminator"},
    )
    dialect = SupportedDialect.POSTGRESQL
    event_data = EventData.shared_data_bytes_from_event(event, dialect)
    decoded = json_loads(event_data)
    expect(decoded["some_data"]).to_equal("withnull")


@test
def from_event_to_db_state() -> None:
    """Test converting event to db state."""
    state = ha.State(
        "sensor.temperature",
        "18",
        context=ha.Context(
            id="01EYQZJXZ5Z1Z1Z1Z1Z1Z1Z1Z1",
            parent_id="01EYQZJXZ5Z1Z1Z1Z1Z1Z1Z1Z1",
            user_id="12345678901234567890123456789012",
        ),
    )
    event = ha.Event(
        EVENT_STATE_CHANGED,
        {"entity_id": "sensor.temperature", "old_state": None, "new_state": state},
        context=state.context,
    )
    db_state = States.from_event(event)
    # Set entity_id, it's set to None by States.from_event
    db_state.entity_id = state.entity_id
    expect(state.as_dict()).to_equal(db_state_to_native(db_state).as_dict())


@test
def from_event_to_db_state_attributes() -> None:
    """Test converting event to db state attributes."""
    attrs = {"this_attr": True}
    state = ha.State("sensor.temperature", "18", attrs)
    event = ha.Event(
        EVENT_STATE_CHANGED,
        {"entity_id": "sensor.temperature", "old_state": None, "new_state": state},
        context=state.context,
    )
    db_attrs = StateAttributes()
    dialect = SupportedDialect.MYSQL

    db_attrs.shared_attrs = StateAttributes.shared_attrs_bytes_from_event(
        event, dialect
    )
    expect(db_state_attributes_to_native(db_attrs)).to_equal(attrs)


@test
def from_event_to_db_state_attributes_with_null() -> None:
    """Test converting a state to StateAttributes with a null with PostgreSQL."""
    attrs = {"this_attr": "withnull\0terminator"}
    state = ha.State("sensor.temperature", "18", attrs)
    event = ha.Event(
        EVENT_STATE_CHANGED,
        {"entity_id": "sensor.temperature", "old_state": None, "new_state": state},
        context=state.context,
    )
    dialect = SupportedDialect.POSTGRESQL
    shared_attrs = StateAttributes.shared_attrs_bytes_from_event(event, dialect)
    decoded = json_loads(shared_attrs)
    expect(decoded["this_attr"]).to_equal("withnull")


@test
def repr_test() -> None:
    """Test converting event to db state repr."""
    attrs = {"this_attr": True}
    fixed_time = datetime(2016, 7, 9, 11, 0, 0, tzinfo=dt_util.UTC, microsecond=432432)
    state = ha.State(
        "sensor.temperature",
        "18",
        attrs,
        last_changed=fixed_time,
        last_updated=fixed_time,
    )
    event = ha.Event(
        EVENT_STATE_CHANGED,
        {"entity_id": "sensor.temperature", "old_state": None, "new_state": state},
        context=state.context,
        time_fired_timestamp=fixed_time.timestamp(),
    )
    expect("2016-07-09 11:00:00+00:00" in repr(States.from_event(event))).to_be(True)
    expect("2016-07-09 11:00:00+00:00" in repr(Events.from_event(event))).to_be(True)


@test
def states_repr_without_timestamp() -> None:
    """Test repr for a state without last_updated_ts."""
    fixed_time = datetime(2016, 7, 9, 11, 0, 0, tzinfo=dt_util.UTC, microsecond=432432)
    states = States(
        entity_id="sensor.temp",
        attributes=None,
        context_id=None,
        context_user_id=None,
        context_parent_id=None,
        origin_idx=None,
        last_updated=fixed_time,
        last_changed=fixed_time,
        last_updated_ts=None,
        last_changed_ts=None,
    )
    expect("2016-07-09 11:00:00+00:00" in repr(states)).to_be(True)


@test
def events_repr_without_timestamp() -> None:
    """Test repr for an event without time_fired_ts."""
    fixed_time = datetime(2016, 7, 9, 11, 0, 0, tzinfo=dt_util.UTC, microsecond=432432)
    events = Events(
        event_type="any",
        event_data=None,
        origin_idx=None,
        time_fired=fixed_time,
        time_fired_ts=None,
        context_id=None,
        context_user_id=None,
        context_parent_id=None,
    )
    expect("2016-07-09 11:00:00+00:00" in repr(events)).to_be(True)


@test
def handling_broken_json_state_attributes() -> None:
    """Test we handle broken json in state attributes."""
    state_attributes = StateAttributes(
        attributes_id=444, hash=1234, shared_attrs="{NOT_PARSE}"
    )
    expect(lambda: db_state_attributes_to_native(state_attributes)).to_raise(
        JSON_DECODE_EXCEPTIONS[0]
    )


@test
def from_event_to_delete_state() -> None:
    """Test converting deleting state event to db state."""
    event = ha.Event(
        EVENT_STATE_CHANGED,
        {
            "entity_id": "sensor.temperature",
            "old_state": ha.State("sensor.temperature", "18"),
            "new_state": None,
        },
    )
    db_state = States.from_event(event)

    expect(db_state.entity_id).to_be_none()
    expect(db_state.state).to_equal("")
    expect(db_state.last_changed_ts).to_be_none()
    expect(abs(db_state.last_updated_ts - event.time_fired.timestamp()) < 1e-6).to_be(
        True
    )


@test
def states_from_native_invalid_entity_id() -> None:
    """Test loading a state from an invalid entity ID."""
    state = States()
    state.entity_id = "test.invalid__id"
    state.attributes = "{}"
    expect(lambda: db_state_to_native(state)).to_raise(InvalidEntityFormatError)

    state = db_state_to_native(state, validate_entity_id=False)
    expect(state.entity_id).to_equal("test.invalid__id")


@test
async def process_timestamp_test() -> None:
    """Test processing time stamp to UTC."""
    datetime_with_tzinfo = datetime(2016, 7, 9, 11, 0, 0, tzinfo=dt_util.UTC)
    datetime_without_tzinfo = datetime(2016, 7, 9, 11, 0, 0)
    est = dt_util.get_time_zone("US/Eastern")
    datetime_est_timezone = datetime(2016, 7, 9, 11, 0, 0, tzinfo=est)
    nst = dt_util.get_time_zone("Canada/Newfoundland")
    datetime_nst_timezone = datetime(2016, 7, 9, 11, 0, 0, tzinfo=nst)
    hst = dt_util.get_time_zone("US/Hawaii")
    datetime_hst_timezone = datetime(2016, 7, 9, 11, 0, 0, tzinfo=hst)

    expect(process_timestamp(datetime_with_tzinfo)).to_equal(
        datetime(2016, 7, 9, 11, 0, 0, tzinfo=dt_util.UTC)
    )
    expect(process_timestamp(datetime_without_tzinfo)).to_equal(
        datetime(2016, 7, 9, 11, 0, 0, tzinfo=dt_util.UTC)
    )
    expect(process_timestamp(datetime_est_timezone)).to_equal(
        datetime(2016, 7, 9, 15, 0, tzinfo=dt_util.UTC)
    )
    expect(process_timestamp(datetime_nst_timezone)).to_equal(
        datetime(2016, 7, 9, 13, 30, tzinfo=dt_util.UTC)
    )
    expect(process_timestamp(datetime_hst_timezone)).to_equal(
        datetime(2016, 7, 9, 21, 0, tzinfo=dt_util.UTC)
    )
    expect(process_timestamp(None)).to_be_none()


@test
async def process_timestamp_to_utc_isoformat_test() -> None:
    """Test processing time stamp to UTC isoformat."""
    datetime_with_tzinfo = datetime(2016, 7, 9, 11, 0, 0, tzinfo=dt_util.UTC)
    datetime_without_tzinfo = datetime(2016, 7, 9, 11, 0, 0)
    est = dt_util.get_time_zone("US/Eastern")
    datetime_est_timezone = datetime(2016, 7, 9, 11, 0, 0, tzinfo=est)
    est = dt_util.get_time_zone("US/Eastern")
    datetime_est_timezone = datetime(2016, 7, 9, 11, 0, 0, tzinfo=est)
    nst = dt_util.get_time_zone("Canada/Newfoundland")
    datetime_nst_timezone = datetime(2016, 7, 9, 11, 0, 0, tzinfo=nst)
    hst = dt_util.get_time_zone("US/Hawaii")
    datetime_hst_timezone = datetime(2016, 7, 9, 11, 0, 0, tzinfo=hst)

    expect(process_timestamp_to_utc_isoformat(datetime_with_tzinfo)).to_equal(
        "2016-07-09T11:00:00+00:00"
    )
    expect(process_timestamp_to_utc_isoformat(datetime_without_tzinfo)).to_equal(
        "2016-07-09T11:00:00+00:00"
    )
    expect(process_timestamp_to_utc_isoformat(datetime_est_timezone)).to_equal(
        "2016-07-09T15:00:00+00:00"
    )
    expect(process_timestamp_to_utc_isoformat(datetime_nst_timezone)).to_equal(
        "2016-07-09T13:30:00+00:00"
    )
    expect(process_timestamp_to_utc_isoformat(datetime_hst_timezone)).to_equal(
        "2016-07-09T21:00:00+00:00"
    )
    expect(process_timestamp_to_utc_isoformat(None)).to_be_none()


@test
async def event_to_db_model() -> None:
    """Test we can round trip Event conversion."""
    event = ha.Event(
        "state_changed",
        {"some": "attr"},
        ha.EventOrigin.local,
        dt_util.utcnow().timestamp(),
    )
    db_event = Events.from_event(event)
    dialect = SupportedDialect.MYSQL
    db_event.event_data = EventData.shared_data_bytes_from_event(event, dialect)
    db_event.event_type = event.event_type
    native = db_event_to_native(db_event)
    expect(native.as_dict()).to_equal(event.as_dict())

    native = db_event_to_native(Events.from_event(event))
    # data is not set by from_event as its in the event_data table
    native.data = event.data
    native.event_type = event.event_type
    expect(native.as_dict()).to_equal(event.as_dict())


@test
async def lazy_state_handles_include_json(
    caplog=Depends(caplog_fx),
) -> None:
    """Test that the LazyState class handles invalid json."""
    row = PropertyMock(
        entity_id="sensor.invalid",
        shared_attrs="{INVALID_JSON}",
    )
    expect(
        LazyState(row, {}, None, row.entity_id, "", 1, False).attributes
    ).to_equal({})
    expect("Error converting row to state attributes" in caplog.text).to_be(True)


@test
async def lazy_state_can_decode_attributes(
    caplog=Depends(caplog_fx),
) -> None:
    """Test that the LazyState prefers can decode attributes."""
    row = PropertyMock(
        entity_id="sensor.invalid",
        attributes='{"shared":true}',
    )
    expect(
        LazyState(row, {}, None, row.entity_id, "", 1, False).attributes
    ).to_equal({"shared": True})


@test
async def lazy_state_handles_different_last_updated_and_last_changed(
    caplog=Depends(caplog_fx),
) -> None:
    """Test that the LazyState handles different last_updated and last_changed."""
    now = datetime(2021, 6, 12, 3, 4, 1, 323, tzinfo=dt_util.UTC)
    row = PropertyMock(
        entity_id="sensor.valid",
        state="off",
        attributes='{"shared":true}',
        last_updated_ts=now.timestamp(),
        last_reported_ts=now.timestamp(),
        last_changed_ts=(now - timedelta(seconds=60)).timestamp(),
    )
    lstate = LazyState(
        row, {}, None, row.entity_id, row.state, row.last_updated_ts, False
    )
    expect(lstate.as_dict()).to_equal(
        {
            "attributes": {"shared": True},
            "entity_id": "sensor.valid",
            "last_changed": "2021-06-12T03:03:01.000323+00:00",
            "last_updated": "2021-06-12T03:04:01.000323+00:00",
            "state": "off",
        }
    )
    expect(lstate.last_updated.timestamp()).to_equal(row.last_updated_ts)
    expect(lstate.last_changed.timestamp()).to_equal(row.last_changed_ts)
    expect(lstate.last_reported.timestamp()).to_equal(row.last_updated_ts)
    expect(lstate.as_dict()).to_equal(
        {
            "attributes": {"shared": True},
            "entity_id": "sensor.valid",
            "last_changed": "2021-06-12T03:03:01.000323+00:00",
            "last_updated": "2021-06-12T03:04:01.000323+00:00",
            "state": "off",
        }
    )
    expect(lstate.last_changed_timestamp).to_equal(row.last_changed_ts)
    expect(lstate.last_updated_timestamp).to_equal(row.last_updated_ts)
    expect(lstate.last_reported_timestamp).to_equal(row.last_updated_ts)


@test
async def lazy_state_handles_same_last_updated_and_last_changed(
    caplog=Depends(caplog_fx),
) -> None:
    """Test that the LazyState handles same last_updated and last_changed."""
    now = datetime(2021, 6, 12, 3, 4, 1, 323, tzinfo=dt_util.UTC)
    row = PropertyMock(
        entity_id="sensor.valid",
        state="off",
        attributes='{"shared":true}',
        last_updated_ts=now.timestamp(),
        last_changed_ts=now.timestamp(),
        last_reported_ts=None,
    )
    lstate = LazyState(
        row, {}, None, row.entity_id, row.state, row.last_updated_ts, False
    )
    expect(lstate.as_dict()).to_equal(
        {
            "attributes": {"shared": True},
            "entity_id": "sensor.valid",
            "last_changed": "2021-06-12T03:04:01.000323+00:00",
            "last_updated": "2021-06-12T03:04:01.000323+00:00",
            "state": "off",
        }
    )
    expect(lstate.last_updated.timestamp()).to_equal(row.last_updated_ts)
    expect(lstate.last_changed.timestamp()).to_equal(row.last_changed_ts)
    expect(lstate.last_reported.timestamp()).to_equal(row.last_updated_ts)
    expect(lstate.as_dict()).to_equal(
        {
            "attributes": {"shared": True},
            "entity_id": "sensor.valid",
            "last_changed": "2021-06-12T03:04:01.000323+00:00",
            "last_updated": "2021-06-12T03:04:01.000323+00:00",
            "state": "off",
        }
    )
    expect(lstate.last_changed_timestamp).to_equal(row.last_changed_ts)
    expect(lstate.last_updated_timestamp).to_equal(row.last_updated_ts)
    expect(lstate.last_reported_timestamp).to_equal(row.last_updated_ts)


@test
async def lazy_state_handles_different_last_reported(
    caplog=Depends(caplog_fx),
) -> None:
    """Test that the LazyState handles last_reported different from last_updated."""
    now = datetime(2021, 6, 12, 3, 4, 1, 323, tzinfo=dt_util.UTC)
    row = PropertyMock(
        entity_id="sensor.valid",
        state="off",
        attributes='{"shared":true}',
        last_updated_ts=(now - timedelta(seconds=60)).timestamp(),
        last_reported_ts=now.timestamp(),
        last_changed_ts=(now - timedelta(seconds=60)).timestamp(),
    )
    lstate = LazyState(
        row, {}, None, row.entity_id, row.state, row.last_updated_ts, False
    )
    expect(lstate.as_dict()).to_equal(
        {
            "attributes": {"shared": True},
            "entity_id": "sensor.valid",
            "last_changed": "2021-06-12T03:03:01.000323+00:00",
            "last_updated": "2021-06-12T03:03:01.000323+00:00",
            "state": "off",
        }
    )
    expect(lstate.last_updated.timestamp()).to_equal(row.last_updated_ts)
    expect(lstate.last_changed.timestamp()).to_equal(row.last_changed_ts)
    expect(lstate.last_reported.timestamp()).to_equal(row.last_reported_ts)
    expect(lstate.last_changed_timestamp).to_equal(row.last_changed_ts)
    expect(lstate.last_updated_timestamp).to_equal(row.last_updated_ts)
    expect(lstate.last_reported_timestamp).to_equal(row.last_reported_ts)
