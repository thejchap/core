"""The tests for the timer component."""

from collections.abc import Callable, Coroutine
from datetime import timedelta
import logging
from typing import Any
from unittest.mock import patch

from freezegun import freeze_time
from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.components.timer import (
    ATTR_DURATION,
    ATTR_FINISHES_AT,
    ATTR_LAST_TRANSITION,
    ATTR_REMAINING,
    ATTR_RESTORE,
    CONF_DURATION,
    CONF_ICON,
    CONF_NAME,
    CONF_RESTORE,
    DEFAULT_DURATION,
    DOMAIN,
    EVENT_TIMER_CANCELLED,
    EVENT_TIMER_CHANGED,
    EVENT_TIMER_FINISHED,
    EVENT_TIMER_PAUSED,
    EVENT_TIMER_RESTARTED,
    EVENT_TIMER_STARTED,
    SERVICE_CANCEL,
    SERVICE_CHANGE,
    SERVICE_FINISH,
    SERVICE_PAUSE,
    SERVICE_START,
    STATUS_ACTIVE,
    STATUS_IDLE,
    STATUS_PAUSED,
    Timer,
)
from homeassistant.const import (
    ATTR_EDITABLE,
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    ATTR_NAME,
    CONF_ENTITY_ID,
    CONF_ID,
    EVENT_STATE_CHANGED,
    SERVICE_RELOAD,
)
from homeassistant.core import Context, CoreState, Event, HomeAssistant, State, callback
from homeassistant.exceptions import HomeAssistantError, Unauthorized
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.restore_state import StoredState, async_get
from homeassistant.setup import async_setup_component
from homeassistant.util.dt import utcnow

from ._fixtures import storage_setup as storage_setup_fx

from tests.common import MockUser, async_capture_events, async_fire_time_changed
from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    freezer as freezer_fixture,
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fx,
    hass_read_only_user as hass_read_only_user_fx,
    hass_ws_client as hass_ws_client_fx,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.typing import WebSocketGenerator

_LOGGER = logging.getLogger(__name__)

FROZEN_TIME = "2023-06-05 17:47:50"


@fixture
def _trigger_executor() -> int:
    """Module-level anchor fixture."""
    return 0


@test.cases(
    test.case("none", invalid_config=None),
    test.case("int", invalid_config=1),
    test.case("name_with_space", invalid_config={"name with space": None}),
)
async def config(
    invalid_config: Any,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config."""
    expect(
        not await async_setup_component(hass, DOMAIN, {DOMAIN: invalid_config})
    ).to_be(True)


@test
async def config_options(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test configuration options."""
    count_start = len(hass.states.async_entity_ids())

    _LOGGER.debug("ENTITIES @ start: %s", hass.states.async_entity_ids())

    config = {
        DOMAIN: {
            "test_1": {},
            "test_2": {
                CONF_NAME: "Hello World",
                CONF_ICON: "mdi:work",
                CONF_DURATION: 10,
            },
            "test_3": None,
        }
    }

    expect(await async_setup_component(hass, "timer", config)).to_be_truthy()
    await hass.async_block_till_done()

    expect(count_start + 3 == len(hass.states.async_entity_ids())).to_be(True)
    await hass.async_block_till_done()

    state_1 = hass.states.get("timer.test_1")
    state_2 = hass.states.get("timer.test_2")
    state_3 = hass.states.get("timer.test_3")

    expect(state_1).not_.to_be_none()
    expect(state_2).not_.to_be_none()
    expect(state_3).not_.to_be_none()

    expect(state_1.state).to_equal(STATUS_IDLE)
    expect(state_1.attributes).to_equal(
        {
            ATTR_DURATION: "0:00:00",
            ATTR_EDITABLE: False,
            ATTR_LAST_TRANSITION: None,
        }
    )

    expect(state_2.state).to_equal(STATUS_IDLE)
    expect(state_2.attributes).to_equal(
        {
            ATTR_DURATION: "0:00:10",
            ATTR_EDITABLE: False,
            ATTR_FRIENDLY_NAME: "Hello World",
            ATTR_ICON: "mdi:work",
            ATTR_LAST_TRANSITION: None,
        }
    )

    expect(state_3.state).to_equal(STATUS_IDLE)
    expect(state_3.attributes).to_equal(
        {
            ATTR_DURATION: str(cv.time_period(DEFAULT_DURATION)),
            ATTR_EDITABLE: False,
            ATTR_LAST_TRANSITION: None,
        }
    )


@test
async def methods_and_events(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test methods and events."""
    with freeze_time(FROZEN_TIME):
        hass.set_state(CoreState.starting)

        await async_setup_component(
            hass, DOMAIN, {DOMAIN: {"test1": {CONF_DURATION: 10}}}
        )

        state = hass.states.get("timer.test1")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATUS_IDLE)
        expect(state.attributes).to_equal(
            {
                ATTR_DURATION: "0:00:10",
                ATTR_EDITABLE: False,
                ATTR_LAST_TRANSITION: None,
            }
        )

        results: list[tuple[Event, State | None]] = []

        @callback
        def fake_event_listener(event: Event):
            """Fake event listener for trigger."""
            results.append((event, hass.states.get("timer.test1")))

        hass.bus.async_listen(EVENT_TIMER_STARTED, fake_event_listener)
        hass.bus.async_listen(EVENT_TIMER_RESTARTED, fake_event_listener)
        hass.bus.async_listen(EVENT_TIMER_PAUSED, fake_event_listener)
        hass.bus.async_listen(EVENT_TIMER_FINISHED, fake_event_listener)
        hass.bus.async_listen(EVENT_TIMER_CANCELLED, fake_event_listener)
        hass.bus.async_listen(EVENT_TIMER_CHANGED, fake_event_listener)

        finish_10 = (utcnow() + timedelta(seconds=10)).isoformat()
        finish_5 = (utcnow() + timedelta(seconds=5)).isoformat()

        steps = [
            {
                "call": SERVICE_START,
                "call_data": {},
                "expected_state": STATUS_ACTIVE,
                "expected_extra_attributes": {
                    ATTR_FINISHES_AT: finish_10,
                    ATTR_LAST_TRANSITION: "started",
                    ATTR_REMAINING: "0:00:10",
                },
                "expected_event": EVENT_TIMER_STARTED,
            },
            {
                "call": SERVICE_PAUSE,
                "call_data": {},
                "expected_state": STATUS_PAUSED,
                "expected_extra_attributes": {
                    ATTR_LAST_TRANSITION: "paused",
                    ATTR_REMAINING: "0:00:10",
                },
                "expected_event": EVENT_TIMER_PAUSED,
            },
            {
                "call": SERVICE_START,
                "call_data": {},
                "expected_state": STATUS_ACTIVE,
                "expected_extra_attributes": {
                    ATTR_FINISHES_AT: finish_10,
                    ATTR_LAST_TRANSITION: "restarted",
                    ATTR_REMAINING: "0:00:10",
                },
                "expected_event": EVENT_TIMER_RESTARTED,
            },
            {
                "call": SERVICE_CANCEL,
                "call_data": {},
                "expected_state": STATUS_IDLE,
                "expected_extra_attributes": {ATTR_LAST_TRANSITION: "cancelled"},
                "expected_event": EVENT_TIMER_CANCELLED,
            },
            {
                "call": SERVICE_CANCEL,
                "call_data": {},
                "expected_state": STATUS_IDLE,
                "expected_extra_attributes": {ATTR_LAST_TRANSITION: "cancelled"},
                "expected_event": None,
            },
            {
                "call": SERVICE_START,
                "call_data": {},
                "expected_state": STATUS_ACTIVE,
                "expected_extra_attributes": {
                    ATTR_FINISHES_AT: finish_10,
                    ATTR_LAST_TRANSITION: "started",
                    ATTR_REMAINING: "0:00:10",
                },
                "expected_event": EVENT_TIMER_STARTED,
            },
            {
                "call": SERVICE_FINISH,
                "call_data": {},
                "expected_state": STATUS_IDLE,
                "expected_extra_attributes": {ATTR_LAST_TRANSITION: "finished"},
                "expected_event": EVENT_TIMER_FINISHED,
            },
            {
                "call": SERVICE_FINISH,
                "call_data": {},
                "expected_state": STATUS_IDLE,
                "expected_extra_attributes": {ATTR_LAST_TRANSITION: "finished"},
                "expected_event": None,
            },
            {
                "call": SERVICE_START,
                "call_data": {},
                "expected_state": STATUS_ACTIVE,
                "expected_extra_attributes": {
                    ATTR_FINISHES_AT: finish_10,
                    ATTR_LAST_TRANSITION: "started",
                    ATTR_REMAINING: "0:00:10",
                },
                "expected_event": EVENT_TIMER_STARTED,
            },
            {
                "call": SERVICE_PAUSE,
                "call_data": {},
                "expected_state": STATUS_PAUSED,
                "expected_extra_attributes": {
                    ATTR_LAST_TRANSITION: "paused",
                    ATTR_REMAINING: "0:00:10",
                },
                "expected_event": EVENT_TIMER_PAUSED,
            },
            {
                "call": SERVICE_CANCEL,
                "call_data": {},
                "expected_state": STATUS_IDLE,
                "expected_extra_attributes": {ATTR_LAST_TRANSITION: "cancelled"},
                "expected_event": EVENT_TIMER_CANCELLED,
            },
            {
                "call": SERVICE_START,
                "call_data": {},
                "expected_state": STATUS_ACTIVE,
                "expected_extra_attributes": {
                    ATTR_FINISHES_AT: finish_10,
                    ATTR_LAST_TRANSITION: "started",
                    ATTR_REMAINING: "0:00:10",
                },
                "expected_event": EVENT_TIMER_STARTED,
            },
            {
                "call": SERVICE_CHANGE,
                "call_data": {CONF_DURATION: -5},
                "expected_state": STATUS_ACTIVE,
                "expected_extra_attributes": {
                    ATTR_FINISHES_AT: finish_5,
                    # Change does not set last_transition
                    ATTR_LAST_TRANSITION: "started",
                    ATTR_REMAINING: "0:00:05",
                },
                "expected_event": EVENT_TIMER_CHANGED,
            },
            {
                "call": SERVICE_START,
                "call_data": {},
                "expected_state": STATUS_ACTIVE,
                "expected_extra_attributes": {
                    ATTR_FINISHES_AT: finish_5,
                    ATTR_LAST_TRANSITION: "restarted",
                    ATTR_REMAINING: "0:00:05",
                },
                "expected_event": EVENT_TIMER_RESTARTED,
            },
            {
                "call": SERVICE_PAUSE,
                "call_data": {},
                "expected_state": STATUS_PAUSED,
                "expected_extra_attributes": {
                    ATTR_LAST_TRANSITION: "paused",
                    ATTR_REMAINING: "0:00:05",
                },
                "expected_event": EVENT_TIMER_PAUSED,
            },
            {
                "call": SERVICE_FINISH,
                "call_data": {},
                "expected_state": STATUS_IDLE,
                "expected_extra_attributes": {ATTR_LAST_TRANSITION: "finished"},
                "expected_event": EVENT_TIMER_FINISHED,
            },
        ]

        expected_events = 0
        for step in steps:
            if step["call"] is not None:
                await hass.services.async_call(
                    DOMAIN,
                    step["call"],
                    {CONF_ENTITY_ID: "timer.test1", **step["call_data"]},
                    blocking=True,
                )
                await hass.async_block_till_done()

            state = hass.states.get("timer.test1")
            expect(state).to_be_truthy()
            if step["expected_state"] is not None:
                expect(state.state).to_equal(step["expected_state"])
                expect(state.attributes).to_equal(
                    {
                        ATTR_DURATION: "0:00:10",
                        ATTR_EDITABLE: False,
                    }
                    | step["expected_extra_attributes"]
                )

            if step["expected_event"] is not None:
                expected_events += 1
                last_result = results[-1]
                event, state = last_result
                expect(event.event_type).to_equal(step["expected_event"])
                expect(state.state).to_equal(step["expected_state"])
                expect(state.attributes).to_equal(
                    {
                        ATTR_DURATION: "0:00:10",
                        ATTR_EDITABLE: False,
                    }
                    | step["expected_extra_attributes"]
                )
                expect(len(results)).to_equal(expected_events)


@test
async def start_service(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test the start/stop service."""
    with freeze_time(FROZEN_TIME):
        await async_setup_component(
            hass, DOMAIN, {DOMAIN: {"test1": {CONF_DURATION: 10}}}
        )

        state = hass.states.get("timer.test1")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATUS_IDLE)
        expect(state.attributes).to_equal(
            {
                ATTR_EDITABLE: False,
                ATTR_DURATION: "0:00:10",
                ATTR_LAST_TRANSITION: None,
            }
        )

        await hass.services.async_call(
            DOMAIN, SERVICE_START, {CONF_ENTITY_ID: "timer.test1"}, blocking=True
        )
        await hass.async_block_till_done()
        state = hass.states.get("timer.test1")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATUS_ACTIVE)
        expect(state.attributes).to_equal(
            {
                ATTR_EDITABLE: False,
                ATTR_DURATION: "0:00:10",
                ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=10)).isoformat(),
                ATTR_LAST_TRANSITION: "started",
                ATTR_REMAINING: "0:00:10",
            }
        )

        await hass.services.async_call(
            DOMAIN, SERVICE_CANCEL, {CONF_ENTITY_ID: "timer.test1"}, blocking=True
        )
        await hass.async_block_till_done()
        state = hass.states.get("timer.test1")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATUS_IDLE)
        expect(state.attributes).to_equal(
            {
                ATTR_EDITABLE: False,
                ATTR_DURATION: "0:00:10",
                ATTR_LAST_TRANSITION: "cancelled",
            }
        )

        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_CHANGE,
                {CONF_ENTITY_ID: "timer.test1", CONF_DURATION: 10},
                blocking=True,
            )

        await hass.services.async_call(
            DOMAIN,
            SERVICE_START,
            {CONF_ENTITY_ID: "timer.test1", CONF_DURATION: 15},
            blocking=True,
        )
        await hass.async_block_till_done()
        state = hass.states.get("timer.test1")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATUS_ACTIVE)
        expect(state.attributes).to_equal(
            {
                ATTR_EDITABLE: False,
                ATTR_DURATION: "0:00:15",
                ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=15)).isoformat(),
                ATTR_LAST_TRANSITION: "started",
                ATTR_REMAINING: "0:00:15",
            }
        )

        async with expect_raises_async(
            HomeAssistantError,
            match="Not possible to change timer timer.test1 beyond duration",
        ):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_CHANGE,
                {CONF_ENTITY_ID: "timer.test1", CONF_DURATION: 20},
                blocking=True,
            )

        async with expect_raises_async(
            HomeAssistantError,
            match="Not possible to change timer timer.test1 to negative time remaining",
        ):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_CHANGE,
                {CONF_ENTITY_ID: "timer.test1", CONF_DURATION: -20},
                blocking=True,
            )

        await hass.services.async_call(
            DOMAIN,
            SERVICE_CHANGE,
            {CONF_ENTITY_ID: "timer.test1", CONF_DURATION: -3},
            blocking=True,
        )
        state = hass.states.get("timer.test1")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATUS_ACTIVE)
        expect(state.attributes).to_equal(
            {
                ATTR_EDITABLE: False,
                ATTR_DURATION: "0:00:15",
                ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=12)).isoformat(),
                # Change does not set last_transition
                ATTR_LAST_TRANSITION: "started",
                ATTR_REMAINING: "0:00:12",
            }
        )

        await hass.services.async_call(
            DOMAIN,
            SERVICE_CHANGE,
            {CONF_ENTITY_ID: "timer.test1", CONF_DURATION: 2},
            blocking=True,
        )
        state = hass.states.get("timer.test1")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATUS_ACTIVE)
        expect(state.attributes).to_equal(
            {
                ATTR_EDITABLE: False,
                ATTR_DURATION: "0:00:15",
                ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=14)).isoformat(),
                # Change does not set last_transition
                ATTR_LAST_TRANSITION: "started",
                ATTR_REMAINING: "0:00:14",
            }
        )

        await hass.services.async_call(
            DOMAIN, SERVICE_CANCEL, {CONF_ENTITY_ID: "timer.test1"}, blocking=True
        )
        await hass.async_block_till_done()
        state = hass.states.get("timer.test1")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATUS_IDLE)
        expect(state.attributes).to_equal(
            {
                ATTR_EDITABLE: False,
                ATTR_DURATION: "0:00:10",
                ATTR_LAST_TRANSITION: "cancelled",
            }
        )

        async with expect_raises_async(
            HomeAssistantError,
            match="Timer timer.test1 is not running, only active timers can be changed",
        ):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_CHANGE,
                {CONF_ENTITY_ID: "timer.test1", CONF_DURATION: 2},
                blocking=True,
            )

        state = hass.states.get("timer.test1")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATUS_IDLE)
        expect(state.attributes).to_equal(
            {
                ATTR_EDITABLE: False,
                ATTR_DURATION: "0:00:10",
                # Change does not set last_transition
                ATTR_LAST_TRANSITION: "cancelled",
            }
        )


@test
async def wait_till_timer_expires(
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test for a timer to end."""
    freezer.move_to(FROZEN_TIME)
    hass.set_state(CoreState.starting)

    await async_setup_component(hass, DOMAIN, {DOMAIN: {"test1": {CONF_DURATION: 20}}})

    state = hass.states.get("timer.test1")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATUS_IDLE)
    expect(state.attributes).to_equal(
        {
            ATTR_DURATION: "0:00:20",
            ATTR_EDITABLE: False,
            ATTR_LAST_TRANSITION: None,
        }
    )

    results = []

    @callback
    def fake_event_listener(event):
        """Fake event listener for trigger."""
        results.append(event)

    hass.bus.async_listen(EVENT_TIMER_STARTED, fake_event_listener)
    hass.bus.async_listen(EVENT_TIMER_PAUSED, fake_event_listener)
    hass.bus.async_listen(EVENT_TIMER_FINISHED, fake_event_listener)
    hass.bus.async_listen(EVENT_TIMER_CANCELLED, fake_event_listener)
    hass.bus.async_listen(EVENT_TIMER_CHANGED, fake_event_listener)

    await hass.services.async_call(
        DOMAIN, SERVICE_START, {CONF_ENTITY_ID: "timer.test1"}, blocking=True
    )
    await hass.async_block_till_done()

    state = hass.states.get("timer.test1")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATUS_ACTIVE)
    expect(state.attributes).to_equal(
        {
            ATTR_DURATION: "0:00:20",
            ATTR_EDITABLE: False,
            ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=20)).isoformat(),
            ATTR_LAST_TRANSITION: "started",
            ATTR_REMAINING: "0:00:20",
        }
    )

    expect(results[-1].event_type).to_equal(EVENT_TIMER_STARTED)
    expect(len(results)).to_equal(1)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_CHANGE,
        {CONF_ENTITY_ID: "timer.test1", CONF_DURATION: -5},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("timer.test1")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATUS_ACTIVE)
    expect(state.attributes).to_equal(
        {
            ATTR_DURATION: "0:00:20",
            ATTR_EDITABLE: False,
            ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=15)).isoformat(),
            ATTR_LAST_TRANSITION: "started",
            ATTR_REMAINING: "0:00:15",
        }
    )

    expect(results[-1].event_type).to_equal(EVENT_TIMER_CHANGED)
    expect(len(results)).to_equal(2)

    freezer.tick(10)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("timer.test1")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATUS_ACTIVE)
    expect(state.attributes).to_equal(
        {
            ATTR_DURATION: "0:00:20",
            ATTR_EDITABLE: False,
            ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=5)).isoformat(),
            ATTR_LAST_TRANSITION: "started",
            ATTR_REMAINING: "0:00:15",
        }
    )

    freezer.tick(20)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("timer.test1")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATUS_IDLE)
    expect(state.attributes).to_equal(
        {
            ATTR_DURATION: "0:00:20",
            ATTR_EDITABLE: False,
            ATTR_LAST_TRANSITION: "finished",
        }
    )

    expect(results[-1].event_type).to_equal(EVENT_TIMER_FINISHED)
    expect(len(results)).to_equal(3)


@test
async def no_initial_state_and_no_restore_state(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure that entity is create without initial and restore feature."""
    hass.set_state(CoreState.starting)

    await async_setup_component(hass, DOMAIN, {DOMAIN: {"test1": {CONF_DURATION: 10}}})

    state = hass.states.get("timer.test1")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATUS_IDLE)
    expect(state.attributes).to_equal(
        {
            ATTR_DURATION: "0:00:10",
            ATTR_EDITABLE: False,
            ATTR_LAST_TRANSITION: None,
        }
    )


@test
async def config_reload(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
    hass_read_only_user: MockUser = Depends(hass_read_only_user_fx),
) -> None:
    """Test reload service."""
    count_start = len(hass.states.async_entity_ids())

    _LOGGER.debug("ENTITIES @ start: %s", hass.states.async_entity_ids())

    config = {
        DOMAIN: {
            "test_1": {},
            "test_2": {
                CONF_NAME: "Hello World",
                CONF_ICON: "mdi:work",
                CONF_DURATION: 10,
            },
        }
    }

    expect(await async_setup_component(hass, "timer", config)).to_be_truthy()
    await hass.async_block_till_done()

    expect(count_start + 2 == len(hass.states.async_entity_ids())).to_be(True)
    await hass.async_block_till_done()

    state_1 = hass.states.get("timer.test_1")
    state_2 = hass.states.get("timer.test_2")
    state_3 = hass.states.get("timer.test_3")

    expect(state_1).not_.to_be_none()
    expect(state_2).not_.to_be_none()
    expect(state_3).to_be_none()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_1")
    ).not_.to_be_none()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_2")
    ).not_.to_be_none()
    expect(entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_3")).to_be_none()

    expect(state_1.state).to_equal(STATUS_IDLE)
    expect(state_1.attributes).to_equal(
        {
            ATTR_DURATION: "0:00:00",
            ATTR_EDITABLE: False,
            ATTR_LAST_TRANSITION: None,
        }
    )

    expect(state_2.state).to_equal(STATUS_IDLE)
    expect(state_2.attributes).to_equal(
        {
            ATTR_DURATION: "0:00:10",
            ATTR_EDITABLE: False,
            ATTR_FRIENDLY_NAME: "Hello World",
            ATTR_ICON: "mdi:work",
            ATTR_LAST_TRANSITION: None,
        }
    )

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: {
                "test_2": {
                    CONF_NAME: "Hello World reloaded",
                    CONF_ICON: "mdi:work-reloaded",
                    CONF_DURATION: 20,
                },
                "test_3": {},
            }
        },
    ):
        async with expect_raises_async(Unauthorized):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_RELOAD,
                blocking=True,
                context=Context(user_id=hass_read_only_user.id),
            )
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id=hass_admin_user.id),
        )
        await hass.async_block_till_done()

    expect(count_start + 2 == len(hass.states.async_entity_ids())).to_be(True)

    state_1 = hass.states.get("timer.test_1")
    state_2 = hass.states.get("timer.test_2")
    state_3 = hass.states.get("timer.test_3")

    expect(state_1).to_be_none()
    expect(state_2).not_.to_be_none()
    expect(state_3).not_.to_be_none()
    expect(entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_1")).to_be_none()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_2")
    ).not_.to_be_none()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_3")
    ).not_.to_be_none()

    expect(state_2.state).to_equal(STATUS_IDLE)
    expect(state_2.attributes).to_equal(
        {
            ATTR_DURATION: "0:00:20",
            ATTR_EDITABLE: False,
            ATTR_FRIENDLY_NAME: "Hello World reloaded",
            ATTR_ICON: "mdi:work-reloaded",
            ATTR_LAST_TRANSITION: None,
        }
    )

    expect(state_3.state).to_equal(STATUS_IDLE)
    expect(state_3.attributes).to_equal(
        {
            ATTR_DURATION: "0:00:00",
            ATTR_EDITABLE: False,
            ATTR_LAST_TRANSITION: None,
        }
    )


@test
async def timer_restarted_event(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Ensure restarted event is called after starting a paused or running timer."""
    with freeze_time(FROZEN_TIME):
        hass.set_state(CoreState.starting)

        await async_setup_component(
            hass, DOMAIN, {DOMAIN: {"test1": {CONF_DURATION: 10}}}
        )

        state = hass.states.get("timer.test1")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATUS_IDLE)
        expect(state.attributes).to_equal(
            {
                ATTR_DURATION: "0:00:10",
                ATTR_EDITABLE: False,
                ATTR_LAST_TRANSITION: None,
            }
        )

        results = []

        @callback
        def fake_event_listener(event):
            """Fake event listener for trigger."""
            results.append(event)

        hass.bus.async_listen(EVENT_TIMER_STARTED, fake_event_listener)
        hass.bus.async_listen(EVENT_TIMER_RESTARTED, fake_event_listener)
        hass.bus.async_listen(EVENT_TIMER_PAUSED, fake_event_listener)
        hass.bus.async_listen(EVENT_TIMER_FINISHED, fake_event_listener)
        hass.bus.async_listen(EVENT_TIMER_CANCELLED, fake_event_listener)

        await hass.services.async_call(
            DOMAIN, SERVICE_START, {CONF_ENTITY_ID: "timer.test1"}
        )
        await hass.async_block_till_done()
        state = hass.states.get("timer.test1")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATUS_ACTIVE)
        expect(state.attributes).to_equal(
            {
                ATTR_DURATION: "0:00:10",
                ATTR_EDITABLE: False,
                ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=10)).isoformat(),
                ATTR_LAST_TRANSITION: "started",
                ATTR_REMAINING: "0:00:10",
            }
        )

        expect(results[-1].event_type).to_equal(EVENT_TIMER_STARTED)
        expect(len(results)).to_equal(1)

        await hass.services.async_call(
            DOMAIN, SERVICE_START, {CONF_ENTITY_ID: "timer.test1"}
        )
        await hass.async_block_till_done()
        state = hass.states.get("timer.test1")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATUS_ACTIVE)
        expect(state.attributes).to_equal(
            {
                ATTR_DURATION: "0:00:10",
                ATTR_EDITABLE: False,
                ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=10)).isoformat(),
                ATTR_LAST_TRANSITION: "restarted",
                ATTR_REMAINING: "0:00:10",
            }
        )

        expect(results[-1].event_type).to_equal(EVENT_TIMER_RESTARTED)
        expect(len(results)).to_equal(2)

        await hass.services.async_call(
            DOMAIN, SERVICE_PAUSE, {CONF_ENTITY_ID: "timer.test1"}
        )
        await hass.async_block_till_done()
        state = hass.states.get("timer.test1")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATUS_PAUSED)
        expect(state.attributes).to_equal(
            {
                ATTR_DURATION: "0:00:10",
                ATTR_EDITABLE: False,
                ATTR_LAST_TRANSITION: "paused",
                ATTR_REMAINING: "0:00:10",
            }
        )

        expect(results[-1].event_type).to_equal(EVENT_TIMER_PAUSED)
        expect(len(results)).to_equal(3)

        await hass.services.async_call(
            DOMAIN, SERVICE_START, {CONF_ENTITY_ID: "timer.test1"}
        )
        await hass.async_block_till_done()
        state = hass.states.get("timer.test1")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATUS_ACTIVE)
        expect(state.attributes).to_equal(
            {
                ATTR_DURATION: "0:00:10",
                ATTR_EDITABLE: False,
                ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=10)).isoformat(),
                ATTR_LAST_TRANSITION: "restarted",
                ATTR_REMAINING: "0:00:10",
            }
        )

        expect(results[-1].event_type).to_equal(EVENT_TIMER_RESTARTED)
        expect(len(results)).to_equal(4)


@test
async def state_changed_when_timer_restarted(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure timer's state changes when it restarted."""
    with freeze_time(FROZEN_TIME):
        hass.set_state(CoreState.starting)

        await async_setup_component(
            hass, DOMAIN, {DOMAIN: {"test1": {CONF_DURATION: 10}}}
        )

        state = hass.states.get("timer.test1")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATUS_IDLE)
        expect(state.attributes).to_equal(
            {
                ATTR_DURATION: "0:00:10",
                ATTR_EDITABLE: False,
                ATTR_LAST_TRANSITION: None,
            }
        )

        results = []

        @callback
        def fake_event_listener(event):
            """Fake event listener for trigger."""
            results.append(event)

        hass.bus.async_listen(EVENT_STATE_CHANGED, fake_event_listener)

        await hass.services.async_call(
            DOMAIN, SERVICE_START, {CONF_ENTITY_ID: "timer.test1"}
        )
        await hass.async_block_till_done()
        state = hass.states.get("timer.test1")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATUS_ACTIVE)
        expect(state.attributes).to_equal(
            {
                ATTR_DURATION: "0:00:10",
                ATTR_EDITABLE: False,
                ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=10)).isoformat(),
                ATTR_LAST_TRANSITION: "started",
                ATTR_REMAINING: "0:00:10",
            }
        )

        expect(results[-1].event_type).to_equal(EVENT_STATE_CHANGED)
        expect(len(results)).to_equal(1)

        await hass.services.async_call(
            DOMAIN, SERVICE_START, {CONF_ENTITY_ID: "timer.test1"}
        )
        await hass.async_block_till_done()
        state = hass.states.get("timer.test1")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATUS_ACTIVE)
        expect(state.attributes).to_equal(
            {
                ATTR_DURATION: "0:00:10",
                ATTR_EDITABLE: False,
                ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=10)).isoformat(),
                ATTR_LAST_TRANSITION: "restarted",
                ATTR_REMAINING: "0:00:10",
            }
        )

        expect(results[-1].event_type).to_equal(EVENT_STATE_CHANGED)
        expect(len(results)).to_equal(2)


@test
async def last_transition_after_restarted_timer_expires(
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test that last_transition changes from restarted to finished when timer expires."""
    freezer.move_to(FROZEN_TIME)
    hass.set_state(CoreState.starting)

    await async_setup_component(hass, DOMAIN, {DOMAIN: {"test1": {CONF_DURATION: 10}}})

    # Start the timer
    await hass.services.async_call(
        DOMAIN, SERVICE_START, {CONF_ENTITY_ID: "timer.test1"}, blocking=True
    )
    await hass.async_block_till_done()

    # Restart the timer
    await hass.services.async_call(
        DOMAIN, SERVICE_START, {CONF_ENTITY_ID: "timer.test1"}, blocking=True
    )
    await hass.async_block_till_done()

    state = hass.states.get("timer.test1")
    expect(state.state).to_equal(STATUS_ACTIVE)
    expect(state.attributes[ATTR_LAST_TRANSITION]).to_equal("restarted")

    # Let the timer expire
    freezer.tick(15)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("timer.test1")
    expect(state.state).to_equal(STATUS_IDLE)
    expect(state.attributes[ATTR_LAST_TRANSITION]).to_equal("finished")


@test
async def last_transition_persists_across_config_update(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that last_transition is preserved when the timer config is updated."""
    with freeze_time(FROZEN_TIME):
        hass.set_state(CoreState.starting)

        await async_setup_component(
            hass, DOMAIN, {DOMAIN: {"test1": {CONF_DURATION: 10}}}
        )

        # Start and cancel to set last_transition to "cancelled"
        await hass.services.async_call(
            DOMAIN, SERVICE_START, {CONF_ENTITY_ID: "timer.test1"}, blocking=True
        )
        await hass.services.async_call(
            DOMAIN, SERVICE_CANCEL, {CONF_ENTITY_ID: "timer.test1"}, blocking=True
        )
        await hass.async_block_till_done()

        state = hass.states.get("timer.test1")
        expect(state.state).to_equal(STATUS_IDLE)
        expect(state.attributes[ATTR_LAST_TRANSITION]).to_equal("cancelled")

        # Reload with a new duration — last_transition should persist
        with patch(
            "homeassistant.config.load_yaml_config_file",
            autospec=True,
            return_value={DOMAIN: {"test1": {CONF_DURATION: 20}}},
        ):
            await hass.services.async_call(DOMAIN, SERVICE_RELOAD, blocking=True)
            await hass.async_block_till_done()

        state = hass.states.get("timer.test1")
        expect(state.state).to_equal(STATUS_IDLE)
        expect(state.attributes[ATTR_DURATION]).to_equal("0:00:20")
        expect(state.attributes[ATTR_LAST_TRANSITION]).to_equal("cancelled")


@test
async def load_from_storage(
    hass: HomeAssistant = Depends(hass_fixture),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test set up from storage."""
    expect(await storage_setup()).to_be_truthy()
    state = hass.states.get(f"{DOMAIN}.timer_from_storage")
    expect(state.state).to_equal(STATUS_IDLE)
    expect(state.attributes).to_equal(
        {
            ATTR_DURATION: "0:00:00",
            ATTR_EDITABLE: True,
            ATTR_FRIENDLY_NAME: "timer from storage",
            ATTR_LAST_TRANSITION: None,
        }
    )


@test
async def editable_state_attribute(
    hass: HomeAssistant = Depends(hass_fixture),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test editable attribute."""
    expect(
        await storage_setup(config={DOMAIN: {"from_yaml": None}})
    ).to_be_truthy()

    state = hass.states.get(f"{DOMAIN}.{DOMAIN}_from_storage")
    expect(state.state).to_equal(STATUS_IDLE)
    expect(state.attributes).to_equal(
        {
            ATTR_DURATION: "0:00:00",
            ATTR_EDITABLE: True,
            ATTR_FRIENDLY_NAME: "timer from storage",
            ATTR_LAST_TRANSITION: None,
        }
    )

    state = hass.states.get(f"{DOMAIN}.from_yaml")
    expect(state.state).to_equal(STATUS_IDLE)
    expect(state.attributes).to_equal(
        {
            ATTR_DURATION: "0:00:00",
            ATTR_EDITABLE: False,
            ATTR_LAST_TRANSITION: None,
        }
    )


@test
async def ws_list(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test listing via WS."""
    expect(
        await storage_setup(config={DOMAIN: {"from_yaml": None}})
    ).to_be_truthy()

    client = await hass_ws_client(hass)

    await client.send_json({"id": 6, "type": f"{DOMAIN}/list"})
    resp = await client.receive_json()
    expect(resp["success"]).to_be_truthy()

    storage_ent = "from_storage"
    yaml_ent = "from_yaml"
    result = {item["id"]: item for item in resp["result"]}

    expect(len(result)).to_equal(1)
    expect(storage_ent in result).to_be_truthy()
    expect(yaml_ent in result).to_be_falsy()
    expect(result[storage_ent][ATTR_NAME]).to_equal("timer from storage")


@test
async def ws_delete(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test WS delete cleans up entity registry."""
    expect(await storage_setup()).to_be_truthy()

    timer_id = "from_storage"
    timer_entity_id = f"{DOMAIN}.{DOMAIN}_{timer_id}"

    state = hass.states.get(timer_entity_id)
    expect(state).not_.to_be_none()
    from_reg = entity_registry.async_get_entity_id(DOMAIN, DOMAIN, timer_id)
    expect(from_reg).to_equal(timer_entity_id)

    client = await hass_ws_client(hass)

    await client.send_json(
        {"id": 6, "type": f"{DOMAIN}/delete", f"{DOMAIN}_id": f"{timer_id}"}
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be_truthy()

    state = hass.states.get(timer_entity_id)
    expect(state).to_be_none()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, timer_id)
    ).to_be_none()


@test
async def update(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test updating timer entity."""
    expect(await storage_setup()).to_be_truthy()

    timer_id = "from_storage"
    timer_entity_id = f"{DOMAIN}.{DOMAIN}_{timer_id}"

    state = hass.states.get(timer_entity_id)
    expect(state.state).to_equal(STATUS_IDLE)
    expect(state.attributes).to_equal(
        {
            ATTR_DURATION: "0:00:00",
            ATTR_EDITABLE: True,
            ATTR_FRIENDLY_NAME: "timer from storage",
            ATTR_LAST_TRANSITION: None,
        }
    )
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, timer_id)
    ).to_equal(timer_entity_id)

    client = await hass_ws_client(hass)

    updated_settings = {
        CONF_NAME: "timer from storage",
        CONF_DURATION: 33,
        CONF_RESTORE: True,
    }
    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": f"{timer_id}",
            **updated_settings,
        }
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be_truthy()
    expect(resp["result"]).to_equal(
        {
            "id": "from_storage",
            CONF_DURATION: "0:00:33",
            CONF_NAME: "timer from storage",
            CONF_RESTORE: True,
        }
    )

    state = hass.states.get(timer_entity_id)
    expect(state.state).to_equal(STATUS_IDLE)
    expect(state.attributes).to_equal(
        {
            ATTR_DURATION: "0:00:33",
            ATTR_EDITABLE: True,
            ATTR_FRIENDLY_NAME: "timer from storage",
            ATTR_LAST_TRANSITION: None,
            ATTR_RESTORE: True,
        }
    )


@test
async def ws_create(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test create WS."""
    expect(await storage_setup(items=[])).to_be_truthy()

    timer_id = "new_timer"
    timer_entity_id = f"{DOMAIN}.{timer_id}"

    state = hass.states.get(timer_entity_id)
    expect(state).to_be_none()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, timer_id)
    ).to_be_none()

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/create",
            CONF_NAME: "New Timer",
            CONF_DURATION: 42,
        }
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be_truthy()

    state = hass.states.get(timer_entity_id)
    expect(state.state).to_equal(STATUS_IDLE)
    expect(state.attributes).to_equal(
        {
            ATTR_DURATION: "0:00:42",
            ATTR_EDITABLE: True,
            ATTR_FRIENDLY_NAME: "New Timer",
            ATTR_LAST_TRANSITION: None,
        }
    )
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, timer_id)
    ).to_equal(timer_entity_id)


@test
async def setup_no_config(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test component setup with no config."""
    count_start = len(hass.states.async_entity_ids())
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()

    with patch(
        "homeassistant.config.load_yaml_config_file", autospec=True, return_value={}
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id=hass_admin_user.id),
        )
        await hass.async_block_till_done()

    expect(count_start == len(hass.states.async_entity_ids())).to_be(True)


@test.cases(
    test.case("none", last_transition=None),
    test.case("cancelled", last_transition="cancelled"),
    test.case("finished", last_transition="finished"),
)
async def restore_idle(
    last_transition: str | None,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test entity restore logic when timer is idle."""
    utc_now = utcnow()
    attrs: dict[str, Any] = {ATTR_DURATION: "0:00:30"}
    if last_transition is not None:
        attrs[ATTR_LAST_TRANSITION] = last_transition
    stored_state = StoredState(
        State("timer.test", STATUS_IDLE, attrs),
        None,
        utc_now,
    )

    data = async_get(hass)
    await data.store.async_save([stored_state.as_dict()])
    await data.async_load()

    entity = Timer.from_storage(
        {
            CONF_ID: "test",
            CONF_NAME: "test",
            CONF_DURATION: "0:01:00",
            CONF_RESTORE: True,
        }
    )
    entity.hass = hass
    entity.entity_id = "timer.test"

    await entity.async_added_to_hass()
    await hass.async_block_till_done()
    expect(entity.state).to_equal(STATUS_IDLE)
    expect(entity.extra_state_attributes).to_equal(
        {
            # Idle timers reset to the configured duration, not the stored one
            ATTR_DURATION: "0:01:00",
            ATTR_EDITABLE: True,
            ATTR_LAST_TRANSITION: last_transition,
            ATTR_RESTORE: True,
        }
    )


@test
async def restore_paused(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test entity restore logic when timer is paused."""
    with freeze_time(FROZEN_TIME):
        utc_now = utcnow()
        stored_state = StoredState(
            State(
                "timer.test",
                STATUS_PAUSED,
                {
                    ATTR_DURATION: "0:00:30",
                    ATTR_LAST_TRANSITION: "paused",
                    ATTR_REMAINING: "0:00:15",
                },
            ),
            None,
            utc_now,
        )

        data = async_get(hass)
        await data.store.async_save([stored_state.as_dict()])
        await data.async_load()

        entity = Timer.from_storage(
            {
                CONF_ID: "test",
                CONF_NAME: "test",
                CONF_DURATION: "0:01:00",
                CONF_RESTORE: True,
            }
        )
        entity.hass = hass
        entity.entity_id = "timer.test"

        await entity.async_added_to_hass()
        await hass.async_block_till_done()
        expect(entity.state).to_equal(STATUS_PAUSED)
        expect(entity.extra_state_attributes).to_equal(
            {
                ATTR_DURATION: "0:00:30",
                ATTR_EDITABLE: True,
                ATTR_LAST_TRANSITION: "paused",
                ATTR_REMAINING: "0:00:15",
                ATTR_RESTORE: True,
            }
        )


@test.cases(
    test.case("none", last_transition=None),
    test.case("started", last_transition="started"),
    test.case("restarted", last_transition="restarted"),
)
async def restore_active_resume(
    last_transition: str | None,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test entity restore logic when timer is active and end time is after startup."""
    with freeze_time(FROZEN_TIME):
        events = async_capture_events(hass, EVENT_TIMER_RESTARTED)
        expect(not events).to_be(True)
        utc_now = utcnow()
        finish = utc_now + timedelta(seconds=30)
        simulated_utc_now = utc_now + timedelta(seconds=15)
        stored_state = StoredState(
            State(
                "timer.test",
                STATUS_ACTIVE,
                {
                    ATTR_DURATION: "0:00:30",
                    ATTR_FINISHES_AT: finish.isoformat(),
                    ATTR_LAST_TRANSITION: last_transition,
                },
            ),
            None,
            utc_now,
        )

        data = async_get(hass)
        await data.store.async_save([stored_state.as_dict()])
        await data.async_load()

        entity = Timer.from_storage(
            {
                CONF_ID: "test",
                CONF_NAME: "test",
                CONF_DURATION: "0:01:00",
                CONF_RESTORE: True,
            }
        )
        entity.hass = hass
        entity.entity_id = "timer.test"

        # In patch make sure we ignore microseconds
        with patch(
            "homeassistant.components.timer.dt_util.utcnow",
            return_value=simulated_utc_now.replace(microsecond=999),
        ):
            await entity.async_added_to_hass()
            await hass.async_block_till_done()

        expect(entity.state).to_equal(STATUS_ACTIVE)
        expect(entity.extra_state_attributes).to_equal(
            {
                ATTR_DURATION: "0:00:30",
                ATTR_EDITABLE: True,
                ATTR_FINISHES_AT: finish.isoformat(),
                ATTR_LAST_TRANSITION: "restarted",
                ATTR_REMAINING: "0:00:15",
                ATTR_RESTORE: True,
            }
        )
        expect(len(events)).to_equal(1)


@test.cases(
    test.case("none", last_transition=None),
    test.case("started", last_transition="started"),
    test.case("restarted", last_transition="restarted"),
)
async def restore_active_finished_outside_grace(
    last_transition: str | None,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test entity restore logic: timer is active, ended while Home Assistant was stopped."""
    events = async_capture_events(hass, EVENT_TIMER_FINISHED)
    expect(not events).to_be(True)
    utc_now = utcnow()
    finish = utc_now + timedelta(seconds=30)
    simulated_utc_now = utc_now + timedelta(seconds=46)
    stored_state = StoredState(
        State(
            "timer.test",
            STATUS_ACTIVE,
            {
                ATTR_DURATION: "0:00:30",
                ATTR_FINISHES_AT: finish.isoformat(),
                ATTR_LAST_TRANSITION: last_transition,
            },
        ),
        None,
        utc_now,
    )

    data = async_get(hass)
    await data.store.async_save([stored_state.as_dict()])
    await data.async_load()

    entity = Timer.from_storage(
        {
            CONF_ID: "test",
            CONF_NAME: "test",
            CONF_DURATION: "0:01:00",
            CONF_RESTORE: True,
        }
    )
    entity.hass = hass
    entity.entity_id = "timer.test"

    with patch(
        "homeassistant.components.timer.dt_util.utcnow", return_value=simulated_utc_now
    ):
        await entity.async_added_to_hass()
        await hass.async_block_till_done()

    expect(entity.state).to_equal(STATUS_IDLE)
    expect(entity.extra_state_attributes).to_equal(
        {
            ATTR_DURATION: "0:01:00",
            ATTR_EDITABLE: True,
            ATTR_LAST_TRANSITION: "finished",
            ATTR_RESTORE: True,
        }
    )
    expect(len(events)).to_equal(1)
