"""The tests for the Demo cover platform."""

from collections.abc import Generator
from datetime import timedelta
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_CURRENT_TILT_POSITION,
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    DOMAIN as COVER_DOMAIN,
    CoverState,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    SERVICE_CLOSE_COVER,
    SERVICE_CLOSE_COVER_TILT,
    SERVICE_OPEN_COVER,
    SERVICE_OPEN_COVER_TILT,
    SERVICE_SET_COVER_POSITION,
    SERVICE_SET_COVER_TILT_POSITION,
    SERVICE_STOP_COVER,
    SERVICE_STOP_COVER_TILT,
    SERVICE_TOGGLE,
    SERVICE_TOGGLE_COVER_TILT,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from ._fixtures import setup_homeassistant

from tests.common import assert_setup_component, async_fire_time_changed
from tests.hass_fixtures import hass as hass_fixture, mock_network

CONFIG = {"cover": {"platform": "demo"}}
ENTITY_COVER = "cover.living_room_window"


@fixture
def cover_only() -> Generator[None]:
    """Enable only the cover platform."""
    with patch(
        "homeassistant.components.demo.COMPONENTS_WITH_CONFIG_ENTRY_DEMO_PLATFORM",
        [Platform.COVER],
    ):
        yield


@fixture
async def setup_comp(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_ha: None = Depends(setup_homeassistant),
    _cover_only: None = Depends(cover_only),
) -> None:
    """Set up demo cover component."""
    with assert_setup_component(1, COVER_DOMAIN):
        await async_setup_component(hass, COVER_DOMAIN, CONFIG)
        await hass.async_block_till_done()


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_comp: None = Depends(setup_comp),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def supported_features(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test cover supported features."""
    state = hass.states.get("cover.garage_door")
    expect(state).not_.to_be(None)
    expect(state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(3)
    state = hass.states.get("cover.kitchen_window")
    expect(state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(11)
    state = hass.states.get("cover.hall_window")
    expect(state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(15)
    state = hass.states.get("cover.living_room_window")
    expect(state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(255)


@test
async def close_cover(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test closing the cover."""
    state = hass.states.get(ENTITY_COVER)
    expect(state.state).to_equal(CoverState.OPEN)
    expect(state.attributes[ATTR_CURRENT_POSITION]).to_equal(70)

    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_CLOSE_COVER, {ATTR_ENTITY_ID: ENTITY_COVER}, blocking=True
    )
    state = hass.states.get(ENTITY_COVER)
    expect(state.state).to_equal(CoverState.CLOSING)
    for _ in range(7):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_COVER)
    expect(state.state).to_equal(CoverState.CLOSED)
    expect(state.attributes[ATTR_CURRENT_POSITION]).to_equal(0)


@test
async def open_cover(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test opening the cover."""
    state = hass.states.get(ENTITY_COVER)
    expect(state.state).to_equal(CoverState.OPEN)
    expect(state.attributes[ATTR_CURRENT_POSITION]).to_equal(70)
    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: ENTITY_COVER}, blocking=True
    )
    state = hass.states.get(ENTITY_COVER)
    expect(state.state).to_equal(CoverState.OPENING)
    for _ in range(7):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_COVER)
    expect(state.state).to_equal(CoverState.OPEN)
    expect(state.attributes[ATTR_CURRENT_POSITION]).to_equal(100)


@test
async def toggle_cover(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test toggling the cover."""
    # Start open
    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: ENTITY_COVER}, blocking=True
    )
    for _ in range(7):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_COVER)
    expect(state.state).to_equal(CoverState.OPEN)
    expect(state.attributes["current_position"]).to_equal(100)
    # Toggle closed
    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: ENTITY_COVER}, blocking=True
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_COVER)
    expect(state.state).to_equal(CoverState.CLOSED)
    expect(state.attributes[ATTR_CURRENT_POSITION]).to_equal(0)
    # Toggle open
    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: ENTITY_COVER}, blocking=True
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_COVER)
    expect(state.state).to_equal(CoverState.OPEN)
    expect(state.attributes[ATTR_CURRENT_POSITION]).to_equal(100)


@test
async def set_cover_position(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test moving the cover to a specific position."""
    state = hass.states.get(ENTITY_COVER)
    expect(state.attributes[ATTR_CURRENT_POSITION]).to_equal(70)
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: ENTITY_COVER, ATTR_POSITION: 10},
        blocking=True,
    )
    for _ in range(6):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_COVER)
    expect(state.attributes[ATTR_CURRENT_POSITION]).to_equal(10)


@test
async def stop_cover(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test stopping the cover."""
    state = hass.states.get(ENTITY_COVER)
    expect(state.attributes[ATTR_CURRENT_POSITION]).to_equal(70)
    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_CLOSE_COVER, {ATTR_ENTITY_ID: ENTITY_COVER}, blocking=True
    )
    future = dt_util.utcnow() + timedelta(seconds=1)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()
    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_STOP_COVER, {ATTR_ENTITY_ID: ENTITY_COVER}, blocking=True
    )
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()
    state = hass.states.get(ENTITY_COVER)
    expect(state.attributes[ATTR_CURRENT_POSITION]).to_equal(60)


@test
async def close_cover_tilt(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test closing the cover tilt."""
    state = hass.states.get(ENTITY_COVER)
    expect(state.attributes[ATTR_CURRENT_TILT_POSITION]).to_equal(50)
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER_TILT,
        {ATTR_ENTITY_ID: ENTITY_COVER},
        blocking=True,
    )
    for _ in range(7):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_COVER)
    expect(state.attributes[ATTR_CURRENT_TILT_POSITION]).to_equal(0)


@test
async def open_cover_tilt(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test opening the cover tilt."""
    state = hass.states.get(ENTITY_COVER)
    expect(state.attributes[ATTR_CURRENT_TILT_POSITION]).to_equal(50)
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER_TILT,
        {ATTR_ENTITY_ID: ENTITY_COVER},
        blocking=True,
    )
    for _ in range(7):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_COVER)
    expect(state.attributes[ATTR_CURRENT_TILT_POSITION]).to_equal(100)


@test
async def toggle_cover_tilt(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test toggling the cover tilt."""
    # Start open
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER_TILT,
        {ATTR_ENTITY_ID: ENTITY_COVER},
        blocking=True,
    )
    for _ in range(7):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_COVER)
    expect(state.attributes[ATTR_CURRENT_TILT_POSITION]).to_equal(100)
    # Toggle closed
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_TOGGLE_COVER_TILT,
        {ATTR_ENTITY_ID: ENTITY_COVER},
        blocking=True,
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_COVER)
    expect(state.attributes[ATTR_CURRENT_TILT_POSITION]).to_equal(0)
    # Toggle open
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_TOGGLE_COVER_TILT,
        {ATTR_ENTITY_ID: ENTITY_COVER},
        blocking=True,
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_COVER)
    expect(state.attributes[ATTR_CURRENT_TILT_POSITION]).to_equal(100)


@test
async def set_cover_tilt_position(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test moving the cover til to a specific position."""
    state = hass.states.get(ENTITY_COVER)
    expect(state.attributes[ATTR_CURRENT_TILT_POSITION]).to_equal(50)
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_TILT_POSITION,
        {ATTR_ENTITY_ID: ENTITY_COVER, ATTR_TILT_POSITION: 90},
        blocking=True,
    )
    for _ in range(7):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_COVER)
    expect(state.attributes[ATTR_CURRENT_TILT_POSITION]).to_equal(90)


@test
async def stop_cover_tilt(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test stopping the cover tilt."""
    state = hass.states.get(ENTITY_COVER)
    expect(state.attributes[ATTR_CURRENT_TILT_POSITION]).to_equal(50)
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER_TILT,
        {ATTR_ENTITY_ID: ENTITY_COVER},
        blocking=True,
    )
    future = dt_util.utcnow() + timedelta(seconds=1)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER_TILT,
        {ATTR_ENTITY_ID: ENTITY_COVER},
        blocking=True,
    )
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()
    state = hass.states.get(ENTITY_COVER)
    expect(state.attributes[ATTR_CURRENT_TILT_POSITION]).to_equal(40)
