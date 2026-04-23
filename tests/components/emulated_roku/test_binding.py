"""Tests for emulated_roku library bindings."""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from tryke import Depends, expect, fixture, test

from homeassistant.components.emulated_roku.binding import (
    ATTR_APP_ID,
    ATTR_COMMAND_TYPE,
    ATTR_KEY,
    ATTR_SOURCE_NAME,
    EVENT_ROKU_COMMAND,
    ROKU_COMMAND_KEYDOWN,
    ROKU_COMMAND_KEYPRESS,
    ROKU_COMMAND_KEYUP,
    ROKU_COMMAND_LAUNCH,
    EmulatedRoku,
)
from homeassistant.core import Event, HomeAssistant, callback

from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def events_fired_properly(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that events are fired correctly."""
    random_name = uuid4().hex
    binding = EmulatedRoku(hass, "x", random_name, "1.2.3.4", 8060, None, None, None)

    events: list[Event] = []
    roku_event_handler = None

    def instantiate(
        event_loop,
        handler,
        roku_usn,
        host_ip,
        listen_port,
        advertise_ip=None,
        advertise_port=None,
        bind_multicast=None,
    ):
        nonlocal roku_event_handler
        roku_event_handler = handler

        return Mock(start=AsyncMock(), close=AsyncMock())

    @callback
    def listener(event: Event) -> None:
        if event.data[ATTR_SOURCE_NAME] == random_name:
            events.append(event)

    with patch(
        "homeassistant.components.emulated_roku.binding.EmulatedRokuServer", instantiate
    ):
        hass.bus.async_listen(EVENT_ROKU_COMMAND, listener)

        result = await binding.setup()
        expect(result).to_be(True)

        expect(roku_event_handler is not None).to_be(True)

        roku_event_handler.on_keydown(random_name, "A")
        roku_event_handler.on_keyup(random_name, "A")
        roku_event_handler.on_keypress(random_name, "C")
        roku_event_handler.launch(random_name, "1")

    await hass.async_block_till_done()

    expect(len(events)).to_equal(4)

    expect(events[0].event_type).to_equal(EVENT_ROKU_COMMAND)
    expect(events[0].data[ATTR_COMMAND_TYPE]).to_equal(ROKU_COMMAND_KEYDOWN)
    expect(events[0].data[ATTR_SOURCE_NAME]).to_equal(random_name)
    expect(events[0].data[ATTR_KEY]).to_equal("A")

    expect(events[1].event_type).to_equal(EVENT_ROKU_COMMAND)
    expect(events[1].data[ATTR_COMMAND_TYPE]).to_equal(ROKU_COMMAND_KEYUP)
    expect(events[1].data[ATTR_SOURCE_NAME]).to_equal(random_name)
    expect(events[1].data[ATTR_KEY]).to_equal("A")

    expect(events[2].event_type).to_equal(EVENT_ROKU_COMMAND)
    expect(events[2].data[ATTR_COMMAND_TYPE]).to_equal(ROKU_COMMAND_KEYPRESS)
    expect(events[2].data[ATTR_SOURCE_NAME]).to_equal(random_name)
    expect(events[2].data[ATTR_KEY]).to_equal("C")

    expect(events[3].event_type).to_equal(EVENT_ROKU_COMMAND)
    expect(events[3].data[ATTR_COMMAND_TYPE]).to_equal(ROKU_COMMAND_LAUNCH)
    expect(events[3].data[ATTR_SOURCE_NAME]).to_equal(random_name)
    expect(events[3].data[ATTR_APP_ID]).to_equal("1")
