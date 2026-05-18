"""The tests for the time automation."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant.components import automation
from homeassistant.components.homeassistant.triggers import time
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from ._fixtures import service_calls, setup_comp

from tests.common import assert_setup_component, async_fire_time_changed
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: None = Depends(setup_comp),
) -> int:
    """Anchor fixture - autouse setup_comp and mock_network for every test."""
    return 0


@test
async def if_fires_using_at(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing at."""
    now = dt_util.now()

    trigger_dt = now.replace(hour=5, minute=0, second=0, microsecond=0) + timedelta(2)
    time_that_will_not_match_right_away = trigger_dt - timedelta(minutes=1)

    freezer.move_to(time_that_will_not_match_right_away)
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "time", "at": "5:00:00"},
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "{{ trigger.platform }} - {{ trigger.now.hour }}",
                            "id": "{{ trigger.id}}",
                        },
                    },
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    async_fire_time_changed(hass, trigger_dt + timedelta(seconds=1))
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("time - 5")
    expect(service_calls[0].data["id"]).to_equal(0)


@test.cases(
    test.case("date_time", has_date=True, has_time=True),
    test.case("date_only", has_date=True, has_time=False),
    test.case("time_only", has_date=False, has_time=True),
)
async def if_fires_using_at_input_datetime(
    has_date: bool,
    has_time: bool,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing at input_datetime."""
    await async_setup_component(
        hass,
        "input_datetime",
        {"input_datetime": {"trigger": {"has_date": has_date, "has_time": has_time}}},
    )
    now = dt_util.now()

    trigger_dt = now.replace(
        hour=5 if has_time else 0, minute=0, second=0, microsecond=0
    ) + timedelta(2)

    await hass.services.async_call(
        "input_datetime",
        "set_datetime",
        {
            ATTR_ENTITY_ID: "input_datetime.trigger",
            "datetime": str(trigger_dt.replace(tzinfo=None)),
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    time_that_will_not_match_right_away = trigger_dt - timedelta(minutes=1)

    some_data = "{{ trigger.platform }}-{{ trigger.now.day }}-{{ trigger.now.hour }}-{{trigger.entity_id}}"

    freezer.move_to(dt_util.as_utc(time_that_will_not_match_right_away))
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "time", "at": "input_datetime.trigger"},
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": some_data},
                    },
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    async_fire_time_changed(hass, trigger_dt + timedelta(seconds=1))
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal(
        f"time-{trigger_dt.day}-{trigger_dt.hour}-input_datetime.trigger"
    )

    if has_date:
        trigger_dt += timedelta(days=1)
    if has_time:
        trigger_dt += timedelta(hours=1)

    await hass.services.async_call(
        "input_datetime",
        "set_datetime",
        {
            ATTR_ENTITY_ID: "input_datetime.trigger",
            "datetime": str(trigger_dt.replace(tzinfo=None)),
        },
        blocking=True,
    )
    expect(len(service_calls)).to_equal(3)
    await hass.async_block_till_done()

    async_fire_time_changed(hass, trigger_dt + timedelta(seconds=1))
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(4)
    expect(service_calls[3].data["some"]).to_equal(
        f"time-{trigger_dt.day}-{trigger_dt.hour}-input_datetime.trigger"
    )


@test.cases(
    test.case(
        "dt_pos10_h0",
        has_date=True,
        has_time=True,
        offset="00:00:10",
        delta=timedelta(seconds=10),
        hour=0,
    ),
    test.case(
        "dt_pos10_h5",
        has_date=True,
        has_time=True,
        offset="00:00:10",
        delta=timedelta(seconds=10),
        hour=5,
    ),
    test.case(
        "dt_pos10_h23",
        has_date=True,
        has_time=True,
        offset="00:00:10",
        delta=timedelta(seconds=10),
        hour=23,
    ),
    test.case(
        "dt_neg10_h0",
        has_date=True,
        has_time=True,
        offset="-00:00:10",
        delta=timedelta(seconds=-10),
        hour=0,
    ),
    test.case(
        "dt_neg10_h5",
        has_date=True,
        has_time=True,
        offset="-00:00:10",
        delta=timedelta(seconds=-10),
        hour=5,
    ),
    test.case(
        "dt_neg10_h23",
        has_date=True,
        has_time=True,
        offset="-00:00:10",
        delta=timedelta(seconds=-10),
        hour=23,
    ),
    test.case(
        "dt_min5_h0",
        has_date=True,
        has_time=True,
        offset={"minutes": 5},
        delta=timedelta(minutes=5),
        hour=0,
    ),
    test.case(
        "dt_min5_h5",
        has_date=True,
        has_time=True,
        offset={"minutes": 5},
        delta=timedelta(minutes=5),
        hour=5,
    ),
    test.case(
        "dt_min5_h23",
        has_date=True,
        has_time=True,
        offset={"minutes": 5},
        delta=timedelta(minutes=5),
        hour=23,
    ),
    test.case(
        "dt_hr1s10_h0",
        has_date=True,
        has_time=True,
        offset="01:00:10",
        delta=timedelta(hours=1, seconds=10),
        hour=0,
    ),
    test.case(
        "dt_hr1s10_h5",
        has_date=True,
        has_time=True,
        offset="01:00:10",
        delta=timedelta(hours=1, seconds=10),
        hour=5,
    ),
    test.case(
        "dt_hr1s10_h23",
        has_date=True,
        has_time=True,
        offset="01:00:10",
        delta=timedelta(hours=1, seconds=10),
        hour=23,
    ),
    test.case(
        "t_pos10_h0",
        has_date=False,
        has_time=True,
        offset="00:00:10",
        delta=timedelta(seconds=10),
        hour=0,
    ),
    test.case(
        "t_pos10_h5",
        has_date=False,
        has_time=True,
        offset="00:00:10",
        delta=timedelta(seconds=10),
        hour=5,
    ),
    test.case(
        "t_pos10_h23",
        has_date=False,
        has_time=True,
        offset="00:00:10",
        delta=timedelta(seconds=10),
        hour=23,
    ),
    test.case(
        "t_neg10_h0",
        has_date=False,
        has_time=True,
        offset="-00:00:10",
        delta=timedelta(seconds=-10),
        hour=0,
    ),
    test.case(
        "t_neg10_h5",
        has_date=False,
        has_time=True,
        offset="-00:00:10",
        delta=timedelta(seconds=-10),
        hour=5,
    ),
    test.case(
        "t_neg10_h23",
        has_date=False,
        has_time=True,
        offset="-00:00:10",
        delta=timedelta(seconds=-10),
        hour=23,
    ),
    test.case(
        "t_min5_h0",
        has_date=False,
        has_time=True,
        offset={"minutes": 5},
        delta=timedelta(minutes=5),
        hour=0,
    ),
    test.case(
        "t_min5_h5",
        has_date=False,
        has_time=True,
        offset={"minutes": 5},
        delta=timedelta(minutes=5),
        hour=5,
    ),
    test.case(
        "t_min5_h23",
        has_date=False,
        has_time=True,
        offset={"minutes": 5},
        delta=timedelta(minutes=5),
        hour=23,
    ),
    test.case(
        "t_hr1s10_h0",
        has_date=False,
        has_time=True,
        offset="01:00:10",
        delta=timedelta(hours=1, seconds=10),
        hour=0,
    ),
    test.case(
        "t_hr1s10_h5",
        has_date=False,
        has_time=True,
        offset="01:00:10",
        delta=timedelta(hours=1, seconds=10),
        hour=5,
    ),
    test.case(
        "t_hr1s10_h23",
        has_date=False,
        has_time=True,
        offset="01:00:10",
        delta=timedelta(hours=1, seconds=10),
        hour=23,
    ),
    test.case(
        "d_pos10_h0",
        has_date=True,
        has_time=False,
        offset="00:00:10",
        delta=timedelta(seconds=10),
        hour=0,
    ),
    test.case(
        "d_pos10_h5",
        has_date=True,
        has_time=False,
        offset="00:00:10",
        delta=timedelta(seconds=10),
        hour=5,
    ),
    test.case(
        "d_pos10_h23",
        has_date=True,
        has_time=False,
        offset="00:00:10",
        delta=timedelta(seconds=10),
        hour=23,
    ),
    test.case(
        "d_neg10_h0",
        has_date=True,
        has_time=False,
        offset="-00:00:10",
        delta=timedelta(seconds=-10),
        hour=0,
    ),
    test.case(
        "d_neg10_h5",
        has_date=True,
        has_time=False,
        offset="-00:00:10",
        delta=timedelta(seconds=-10),
        hour=5,
    ),
    test.case(
        "d_neg10_h23",
        has_date=True,
        has_time=False,
        offset="-00:00:10",
        delta=timedelta(seconds=-10),
        hour=23,
    ),
    test.case(
        "d_min5_h0",
        has_date=True,
        has_time=False,
        offset={"minutes": 5},
        delta=timedelta(minutes=5),
        hour=0,
    ),
    test.case(
        "d_min5_h5",
        has_date=True,
        has_time=False,
        offset={"minutes": 5},
        delta=timedelta(minutes=5),
        hour=5,
    ),
    test.case(
        "d_min5_h23",
        has_date=True,
        has_time=False,
        offset={"minutes": 5},
        delta=timedelta(minutes=5),
        hour=23,
    ),
    test.case(
        "d_hr1s10_h0",
        has_date=True,
        has_time=False,
        offset="01:00:10",
        delta=timedelta(hours=1, seconds=10),
        hour=0,
    ),
    test.case(
        "d_hr1s10_h5",
        has_date=True,
        has_time=False,
        offset="01:00:10",
        delta=timedelta(hours=1, seconds=10),
        hour=5,
    ),
    test.case(
        "d_hr1s10_h23",
        has_date=True,
        has_time=False,
        offset="01:00:10",
        delta=timedelta(hours=1, seconds=10),
        hour=23,
    ),
)
async def if_fires_using_at_input_datetime_with_offset(
    has_date: bool,
    has_time: bool,
    offset: str | dict[str, int],
    delta: timedelta,
    hour: int,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing at input_datetime."""
    await async_setup_component(
        hass,
        "input_datetime",
        {"input_datetime": {"trigger": {"has_date": has_date, "has_time": has_time}}},
    )
    now = dt_util.now()

    start_dt = now.replace(
        hour=hour if has_time else 0, minute=0, second=0, microsecond=0
    ) + timedelta(2)
    trigger_dt = start_dt + delta

    await hass.services.async_call(
        "input_datetime",
        "set_datetime",
        {
            ATTR_ENTITY_ID: "input_datetime.trigger",
            "datetime": str(start_dt.replace(tzinfo=None)),
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    time_that_will_not_match_right_away = trigger_dt - timedelta(minutes=1)

    some_data = "{{ trigger.platform }}-{{ trigger.now.day }}-{{ trigger.now.hour }}-{{trigger.entity_id}}"

    freezer.move_to(dt_util.as_utc(time_that_will_not_match_right_away))
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time",
                        "at": {"entity_id": "input_datetime.trigger", "offset": offset},
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": some_data},
                    },
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    async_fire_time_changed(hass, trigger_dt + timedelta(seconds=1))
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal(
        f"time-{trigger_dt.day}-{trigger_dt.hour}-input_datetime.trigger"
    )


@test.cases(
    test.case(
        "static_times",
        conf_at=["5:00:00", "6:00:00", "{{ '7:00:00' }}"],
        trigger_deltas=[timedelta(0), timedelta(hours=1), timedelta(hours=2)],
    ),
    test.case(
        "with_sensor",
        conf_at=[
            "5:00:05",
            {"entity_id": "sensor.next_alarm", "offset": "00:00:10"},
            "sensor.next_alarm",
        ],
        trigger_deltas=[
            timedelta(seconds=5),
            timedelta(seconds=10),
            timedelta(0),
        ],
    ),
)
async def if_fires_using_multiple_at(
    conf_at: list[str | dict[str, int | str]],
    trigger_deltas: list[timedelta],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing at multiple trigger times."""

    now = dt_util.now()

    start_dt = now.replace(hour=5, minute=0, second=0, microsecond=0) + timedelta(2)

    hass.states.async_set(
        "sensor.next_alarm",
        start_dt.isoformat(),
        {ATTR_DEVICE_CLASS: SensorDeviceClass.TIMESTAMP},
    )

    time_that_will_not_match_right_away = start_dt - timedelta(minutes=1)

    freezer.move_to(dt_util.as_utc(time_that_will_not_match_right_away))
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "time", "at": conf_at},
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "{{ trigger.platform }} - {{ trigger.now.hour }}"
                        },
                    },
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    for count, delta in enumerate(sorted(trigger_deltas)):
        async_fire_time_changed(hass, start_dt + delta + timedelta(seconds=1))
        await hass.async_block_till_done()

        expect(len(service_calls)).to_equal(count + 1)
        expect(service_calls[count].data["some"]).to_equal(
            f"time - {5 + (delta.seconds // 3600)}"
        )


@test
async def if_not_fires_using_wrong_at(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """YAML translates time values to total seconds.

    This should break the before rule.
    """
    now = dt_util.utcnow()

    time_that_will_not_match_right_away = now.replace(
        year=now.year + 1, day=1, hour=1, minute=0, second=0
    )

    freezer.move_to(time_that_will_not_match_right_away)
    with assert_setup_component(1, automation.DOMAIN):
        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: {
                        "trigger": {
                            "platform": "time",
                            "at": 3605,
                            # Total seconds. Hour = 3600 second
                        },
                        "action": {"service": "test.automation"},
                    }
                },
            )
        ).to_be(True)
    await hass.async_block_till_done()
    expect(hass.states.get("automation.automation_0").state).to_equal(STATE_UNAVAILABLE)

    async_fire_time_changed(
        hass, now.replace(year=now.year + 1, day=1, hour=1, minute=0, second=5)
    )

    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test
async def if_action_before(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for if action before."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "condition": {"condition": "time", "before": "10:00"},
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    before_10 = dt_util.now().replace(hour=8)
    after_10 = dt_util.now().replace(hour=14)

    with patch("homeassistant.helpers.condition.dt_util.now", return_value=before_10):
        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)

    with patch("homeassistant.helpers.condition.dt_util.now", return_value=after_10):
        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)


@test
async def if_action_after(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for if action after."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "condition": {"condition": "time", "after": "10:00"},
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    before_10 = dt_util.now().replace(hour=8)
    after_10 = dt_util.now().replace(hour=14)

    with patch("homeassistant.helpers.condition.dt_util.now", return_value=before_10):
        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(0)

    with patch("homeassistant.helpers.condition.dt_util.now", return_value=after_10):
        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)


@test
async def if_action_one_weekday(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for if action with one weekday."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "condition": {"condition": "time", "weekday": "mon"},
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    days_past_monday = dt_util.now().weekday()
    monday = dt_util.now() - timedelta(days=days_past_monday)
    tuesday = monday + timedelta(days=1)

    with patch("homeassistant.helpers.condition.dt_util.now", return_value=monday):
        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)

    with patch("homeassistant.helpers.condition.dt_util.now", return_value=tuesday):
        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)


@test
async def if_action_list_weekday(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for action with a list of weekdays."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "condition": {"condition": "time", "weekday": ["mon", "tue"]},
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    days_past_monday = dt_util.now().weekday()
    monday = dt_util.now() - timedelta(days=days_past_monday)
    tuesday = monday + timedelta(days=1)
    wednesday = tuesday + timedelta(days=1)

    with patch("homeassistant.helpers.condition.dt_util.now", return_value=monday):
        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)

    with patch("homeassistant.helpers.condition.dt_util.now", return_value=tuesday):
        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(2)

    with patch("homeassistant.helpers.condition.dt_util.now", return_value=wednesday):
        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(2)


@test
async def untrack_time_change(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for removing tracked time changes."""
    mock_track_time_change = Mock()
    with patch(
        "homeassistant.components.homeassistant.triggers.time.async_track_time_change",
        return_value=mock_track_time_change,
    ):
        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: {
                        "alias": "test",
                        "trigger": {
                            "platform": "time",
                            "at": ["5:00:00", "6:00:00", "7:00:00"],
                        },
                        "action": {
                            "service": "test.automation",
                            "data": {"test": "test"},
                        },
                    }
                },
            )
        ).to_be(True)
        await hass.async_block_till_done()

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "automation.test"},
        blocking=True,
    )

    expect(len(mock_track_time_change.mock_calls)).to_equal(3)


@test.cases(
    test.case(
        "plain_timestamp",
        at_sensor="sensor.next_alarm",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    test.case(
        "plain_uptime",
        at_sensor="sensor.next_alarm",
        device_class=SensorDeviceClass.UPTIME,
    ),
    test.case(
        "tmpl_timestamp",
        at_sensor="{{ 'sensor.next_alarm' }}",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    test.case(
        "tmpl_uptime",
        at_sensor="{{ 'sensor.next_alarm' }}",
        device_class=SensorDeviceClass.UPTIME,
    ),
)
async def if_fires_using_at_sensor(
    at_sensor: str,
    device_class: SensorDeviceClass,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing at sensor time."""
    now = dt_util.now()

    trigger_dt = now.replace(hour=5, minute=0, second=0, microsecond=0) + timedelta(2)

    hass.states.async_set(
        "sensor.next_alarm",
        trigger_dt.isoformat(),
        {ATTR_DEVICE_CLASS: device_class},
    )

    time_that_will_not_match_right_away = trigger_dt - timedelta(minutes=1)

    some_data = "{{ trigger.platform }}-{{ trigger.now.day }}-{{ trigger.now.hour }}-{{trigger.entity_id}}"

    freezer.move_to(dt_util.as_utc(time_that_will_not_match_right_away))
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "time", "at": at_sensor},
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": some_data},
                    },
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    async_fire_time_changed(hass, trigger_dt + timedelta(seconds=1))
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal(
        f"time-{trigger_dt.day}-{trigger_dt.hour}-sensor.next_alarm"
    )

    trigger_dt += timedelta(days=1, hours=1)

    hass.states.async_set(
        "sensor.next_alarm",
        trigger_dt.isoformat(),
        {ATTR_DEVICE_CLASS: device_class},
    )
    await hass.async_block_till_done()

    async_fire_time_changed(hass, trigger_dt + timedelta(seconds=1))
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal(
        f"time-{trigger_dt.day}-{trigger_dt.hour}-sensor.next_alarm"
    )

    for broken in ("unknown", "unavailable", "invalid-ts"):
        hass.states.async_set(
            "sensor.next_alarm",
            trigger_dt.isoformat(),
            {ATTR_DEVICE_CLASS: device_class},
        )
        await hass.async_block_till_done()
        hass.states.async_set(
            "sensor.next_alarm",
            broken,
            {ATTR_DEVICE_CLASS: device_class},
        )
        await hass.async_block_till_done()

        async_fire_time_changed(hass, trigger_dt + timedelta(seconds=1))
        await hass.async_block_till_done()

        # We should not have listened to anything
        expect(len(service_calls)).to_equal(2)

    # Now without device class
    hass.states.async_set(
        "sensor.next_alarm",
        trigger_dt.isoformat(),
        {ATTR_DEVICE_CLASS: device_class},
    )
    await hass.async_block_till_done()
    hass.states.async_set(
        "sensor.next_alarm",
        trigger_dt.isoformat(),
    )
    await hass.async_block_till_done()

    async_fire_time_changed(hass, trigger_dt + timedelta(seconds=1))
    await hass.async_block_till_done()

    # We should not have listened to anything
    expect(len(service_calls)).to_equal(2)


@test.cases(
    test.case(
        "pos10_ts",
        offset="00:00:10",
        delta=timedelta(seconds=10),
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    test.case(
        "neg10_ts",
        offset="-00:00:10",
        delta=timedelta(seconds=-10),
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    test.case(
        "min5_ts",
        offset={"minutes": 5},
        delta=timedelta(minutes=5),
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    test.case(
        "pos10_up",
        offset="00:00:10",
        delta=timedelta(seconds=10),
        device_class=SensorDeviceClass.UPTIME,
    ),
    test.case(
        "neg10_up",
        offset="-00:00:10",
        delta=timedelta(seconds=-10),
        device_class=SensorDeviceClass.UPTIME,
    ),
    test.case(
        "min5_up",
        offset={"minutes": 5},
        delta=timedelta(minutes=5),
        device_class=SensorDeviceClass.UPTIME,
    ),
)
async def if_fires_using_at_sensor_with_offset(
    offset: str | dict[str, int],
    delta: timedelta,
    device_class: SensorDeviceClass,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing at sensor time."""
    now = dt_util.now()

    start_dt = now.replace(hour=5, minute=0, second=0, microsecond=0) + timedelta(2)
    trigger_dt = start_dt + delta

    hass.states.async_set(
        "sensor.next_alarm",
        start_dt.isoformat(),
        {ATTR_DEVICE_CLASS: device_class},
    )

    time_that_will_not_match_right_away = trigger_dt - timedelta(minutes=1)

    some_data = "{{ trigger.platform }}-{{ trigger.now.day }}-{{ trigger.now.hour }}-{{ trigger.now.minute }}-{{ trigger.now.second }}-{{trigger.entity_id}}"

    freezer.move_to(dt_util.as_utc(time_that_will_not_match_right_away))
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time",
                        "at": {
                            "entity_id": "sensor.next_alarm",
                            "offset": offset,
                        },
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": some_data},
                    },
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    async_fire_time_changed(hass, trigger_dt + timedelta(seconds=1))
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal(
        f"time-{trigger_dt.day}-{trigger_dt.hour}-{trigger_dt.minute}-{trigger_dt.second}-sensor.next_alarm"
    )

    start_dt += timedelta(days=1, hours=1)
    trigger_dt += timedelta(days=1, hours=1)

    hass.states.async_set(
        "sensor.next_alarm",
        start_dt.isoformat(),
        {ATTR_DEVICE_CLASS: device_class},
    )
    await hass.async_block_till_done()

    async_fire_time_changed(hass, trigger_dt + timedelta(seconds=1))
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal(
        f"time-{trigger_dt.day}-{trigger_dt.hour}-{trigger_dt.minute}-{trigger_dt.second}-sensor.next_alarm"
    )


@test.cases(
    test.case("input_datetime", conf={"platform": "time", "at": "input_datetime.bla"}),
    test.case("sensor", conf={"platform": "time", "at": "sensor.bla"}),
    test.case("time_str", conf={"platform": "time", "at": "12:34"}),
    test.case("tmpl_time", conf={"platform": "time", "at": "{{ '12:34' }}"}),
    test.case(
        "tmpl_input_dt", conf={"platform": "time", "at": "{{ 'input_datetime.bla' }}"}
    ),
    test.case("tmpl_sensor", conf={"platform": "time", "at": "{{ 'sensor.bla' }}"}),
    test.case(
        "sensor_offset",
        conf={
            "platform": "time",
            "at": {"entity_id": "sensor.bla", "offset": "-00:01"},
        },
    ),
    test.case(
        "list_sensor_offset",
        conf={
            "platform": "time",
            "at": [{"entity_id": "sensor.bla", "offset": "-01:00:00"}],
        },
    ),
)
def schema_valid(conf: dict) -> None:
    """Make sure we don't accept number for 'at' value."""
    time.TRIGGER_SCHEMA(conf)


@test.cases(
    test.case(
        "binary_sensor", conf={"platform": "time", "at": "binary_sensor.bla"}
    ),
    test.case("number", conf={"platform": "time", "at": 745}),
    test.case("bad_hour", conf={"platform": "time", "at": "25:00"}),
    test.case(
        "time_as_entity",
        conf={
            "platform": "time",
            "at": {"entity_id": "13:00:00", "offset": "0:10"},
        },
    ),
)
def schema_invalid(conf: dict) -> None:
    """Make sure we don't accept number for 'at' value."""
    expect(lambda: time.TRIGGER_SCHEMA(conf)).to_raise(vol.Invalid)


@test
async def datetime_in_past_on_load(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test time trigger works if input_datetime is in past."""
    await async_setup_component(
        hass,
        "input_datetime",
        {"input_datetime": {"my_trigger": {"has_date": True, "has_time": True}}},
    )

    now = dt_util.now()
    past = now - timedelta(days=2)
    future = now + timedelta(days=1)

    await hass.services.async_call(
        "input_datetime",
        "set_datetime",
        {
            ATTR_ENTITY_ID: "input_datetime.my_trigger",
            "datetime": str(past.replace(tzinfo=None)),
        },
        blocking=True,
    )
    expect(len(service_calls)).to_equal(1)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "time", "at": "input_datetime.my_trigger"},
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "{{ trigger.platform }}-{{ trigger.now.day }}-{{ trigger.now.hour }}-{{trigger.entity_id}}"
                        },
                    },
                }
            },
        )
    ).to_be(True)

    async_fire_time_changed(hass, now)
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)

    await hass.services.async_call(
        "input_datetime",
        "set_datetime",
        {
            ATTR_ENTITY_ID: "input_datetime.my_trigger",
            "datetime": str(future.replace(tzinfo=None)),
        },
        blocking=True,
    )
    expect(len(service_calls)).to_equal(2)
    await hass.async_block_till_done()

    async_fire_time_changed(hass, future + timedelta(seconds=1))
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(3)
    expect(service_calls[2].data["some"]).to_equal(
        f"time-{future.day}-{future.hour}-input_datetime.my_trigger"
    )


@test.cases(
    test.case("hello", trigger={"platform": "time", "at": "{{ 'hello world' }}"}),
    test.case("number", trigger={"platform": "time", "at": "{{ 74 }}"}),
    test.case("bool", trigger={"platform": "time", "at": "{{ true }}"}),
    test.case("float", trigger={"platform": "time", "at": "{{ 7.5465 }}"}),
)
async def if_at_template_renders_bad_value(
    trigger: dict[str, str],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test for invalid templates."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": trigger,
                    "action": {
                        "service": "test.automation",
                    },
                }
            },
        )
    ).to_be(True)

    await hass.async_block_till_done()

    expect(
        "expected HH:MM, HH:MM:SS or Entity ID with domain 'input_datetime' or 'sensor'"
        in caplog.text
    ).to_be(True)


@test.cases(
    test.case(
        "strftime", trigger={"platform": "time", "at": "{{ now().strftime('%H:%M') }}"}
    ),
    test.case(
        "states",
        trigger={"platform": "time", "at": "{{ states('sensor.blah') | int(0) }}"},
    ),
)
async def if_at_template_limited_template(
    trigger: dict[str, str],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test for invalid templates."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": trigger,
                    "action": {
                        "service": "test.automation",
                    },
                }
            },
        )
    ).to_be(True)

    await hass.async_block_till_done()

    expect("is not supported in limited templates" in caplog.text).to_be(True)


@test
async def if_fires_using_weekday_single(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on a specific weekday."""
    # Freeze time to Monday, January 2, 2023 at 5:00:00
    monday_trigger = dt_util.as_utc(datetime(2023, 1, 2, 5, 0, 0, 0))

    freezer.move_to(monday_trigger)

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "time", "at": "5:00:00", "weekday": "mon"},
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "{{ trigger.platform }} - {{ trigger.now.strftime('%A') }}",
                        },
                    },
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    # Fire the trigger on Monday
    async_fire_time_changed(hass, monday_trigger + timedelta(seconds=1))
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("time - Monday")

    # Fire on Tuesday at the same time - should not trigger
    tuesday_trigger = dt_util.as_utc(datetime(2023, 1, 3, 5, 0, 0, 0))
    async_fire_time_changed(hass, tuesday_trigger)
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_using_weekday_multiple(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on multiple weekdays."""
    # Freeze time to Monday, January 2, 2023 at 5:00:00
    monday_trigger = dt_util.as_utc(datetime(2023, 1, 2, 5, 0, 0, 0))

    freezer.move_to(monday_trigger)

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time",
                        "at": "5:00:00",
                        "weekday": ["mon", "wed", "fri"],
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "{{ trigger.platform }} - {{ trigger.now.strftime('%A') }}",
                        },
                    },
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    # Fire on Monday - should trigger
    async_fire_time_changed(hass, monday_trigger + timedelta(seconds=1))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect("Monday" in service_calls[0].data["some"]).to_be(True)

    # Fire on Tuesday - should not trigger
    tuesday_trigger = dt_util.as_utc(datetime(2023, 1, 3, 5, 0, 0, 0))
    async_fire_time_changed(hass, tuesday_trigger)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    # Fire on Wednesday - should trigger
    wednesday_trigger = dt_util.as_utc(datetime(2023, 1, 4, 5, 0, 0, 0))
    async_fire_time_changed(hass, wednesday_trigger)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect("Wednesday" in service_calls[1].data["some"]).to_be(True)

    # Fire on Friday - should trigger
    friday_trigger = dt_util.as_utc(datetime(2023, 1, 6, 5, 0, 0, 0))
    async_fire_time_changed(hass, friday_trigger)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(3)
    expect("Friday" in service_calls[2].data["some"]).to_be(True)


@test
async def if_fires_using_weekday_with_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on weekday with input_datetime entity."""
    await async_setup_component(
        hass,
        "input_datetime",
        {"input_datetime": {"trigger": {"has_date": False, "has_time": True}}},
    )

    # Freeze time to Monday, January 2, 2023 at 5:00:00
    monday_trigger = dt_util.as_utc(datetime(2023, 1, 2, 5, 0, 0, 0))

    await hass.services.async_call(
        "input_datetime",
        "set_datetime",
        {
            ATTR_ENTITY_ID: "input_datetime.trigger",
            "time": "05:00:00",
        },
        blocking=True,
    )

    freezer.move_to(monday_trigger)

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time",
                        "at": "input_datetime.trigger",
                        "weekday": "mon",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "{{ trigger.platform }} - {{ trigger.now.strftime('%A') }}",
                            "entity": "{{ trigger.entity_id }}",
                        },
                    },
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    # Fire on Monday - should trigger
    async_fire_time_changed(hass, monday_trigger + timedelta(seconds=1))
    await hass.async_block_till_done()
    automation_calls = [call for call in service_calls if call.domain == "test"]
    expect(len(automation_calls)).to_equal(1)
    expect("Monday" in automation_calls[0].data["some"]).to_be(True)
    expect(automation_calls[0].data["entity"]).to_equal("input_datetime.trigger")

    # Fire on Tuesday - should not trigger
    tuesday_trigger = dt_util.as_utc(datetime(2023, 1, 3, 5, 0, 0, 0))
    async_fire_time_changed(hass, tuesday_trigger)
    await hass.async_block_till_done()
    automation_calls = [call for call in service_calls if call.domain == "test"]
    expect(len(automation_calls)).to_equal(1)


@test
def weekday_validation() -> None:
    """Test weekday validation in trigger schema."""
    # Valid single weekday
    valid_config = {"platform": "time", "at": "5:00:00", "weekday": "mon"}
    time.TRIGGER_SCHEMA(valid_config)

    # Valid multiple weekdays
    valid_config = {
        "platform": "time",
        "at": "5:00:00",
        "weekday": ["mon", "wed", "fri"],
    }
    time.TRIGGER_SCHEMA(valid_config)

    # Invalid weekday
    invalid_config = {"platform": "time", "at": "5:00:00", "weekday": "invalid"}
    expect(lambda: time.TRIGGER_SCHEMA(invalid_config)).to_raise(vol.Invalid)

    # Invalid weekday in list
    invalid_config_2 = {
        "platform": "time",
        "at": "5:00:00",
        "weekday": ["mon", "invalid"],
    }
    expect(lambda: time.TRIGGER_SCHEMA(invalid_config_2)).to_raise(vol.Invalid)
