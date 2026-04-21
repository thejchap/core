"""The tests for the Restore component."""

from collections.abc import Coroutine
from datetime import datetime, timedelta
import logging
from typing import Any
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.const import EVENT_HOMEASSISTANT_START, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import CoreState, HomeAssistant, State
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.reload import async_get_platform_without_config_entry
from homeassistant.helpers.restore_state import (
    DATA_RESTORE_STATE,
    STORAGE_KEY,
    ExtraStoredData,
    RestoreEntity,
    RestoreStateData,
    StoredState,
    async_get,
    async_load,
)
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util

from tests.common import (
    MockEntityPlatform,
    MockModule,
    MockPlatform,
    async_fire_time_changed,
    json_round_trip,
    mock_integration,
    mock_platform,
)
from tests.hass_fixtures import LogCapture, caplog, hass, hass_storage

_LOGGER = logging.getLogger(__name__)
DOMAIN = "test_domain"
PLATFORM = "test_platform"


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def caching_data(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that we cache data."""
    now = dt_util.utcnow()
    stored_states = [
        StoredState(State("input_boolean.b0", "on"), None, now),
        StoredState(State("input_boolean.b1", "on"), None, now),
        StoredState(State("input_boolean.b2", "on"), None, now),
    ]

    data = async_get(hass)
    await hass.async_block_till_done()
    await data.store.async_save([state.as_dict() for state in stored_states])

    # Emulate a fresh load
    hass.data.pop(DATA_RESTORE_STATE)

    with (
        patch(
            "homeassistant.helpers.restore_state.Store.async_load",
            side_effect=HomeAssistantError,
        ),
        patch("homeassistant.helpers.restore_state.Store.async_save"),
    ):
        # Failure to load should not be treated as fatal
        await async_load(hass)

    data = async_get(hass)
    expect(data.last_states).to_equal({})

    # Mock that only b1 is present this run
    with patch(
        "homeassistant.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        await async_load(hass)
        await hass.async_block_till_done()

    data = async_get(hass)

    entity = RestoreEntity()
    entity.hass = hass
    entity.entity_id = "input_boolean.b1"

    # Mock that only b1 is present this run
    state = await entity.async_get_last_state()

    expect(state).not_.to_be_none()
    expect(state.entity_id).to_equal("input_boolean.b1")
    expect(state.state).to_equal("on")

    expect(mock_write_data.called).to_be_truthy()


@test
async def periodic_write(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that we write periodiclly but not after stop."""
    data = async_get(hass)
    await hass.async_block_till_done()
    await data.store.async_save([])

    # Emulate a fresh load
    with patch(
        "homeassistant.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        hass.data.pop(DATA_RESTORE_STATE)
        await async_load(hass)
        data = async_get(hass)

        entity = RestoreEntity()
        entity.hass = hass
        entity.entity_id = "input_boolean.b1"

        await entity.async_get_last_state()
        await hass.async_block_till_done()

    expect(mock_write_data.called).to_be_truthy()

    with patch(
        "homeassistant.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=15))
        await hass.async_block_till_done()

    expect(mock_write_data.called).to_be_truthy()

    with patch(
        "homeassistant.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
        await hass.async_block_till_done()

    expect(mock_write_data.called).to_be_truthy()

    with patch(
        "homeassistant.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=30))
        await hass.async_block_till_done()

    expect(mock_write_data.called).to_be_falsy()


@test
async def save_persistent_states(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that we cancel the currently running job, save the data, and verify the perdiodic job continues."""
    data = async_get(hass)
    await hass.async_block_till_done()
    await data.store.async_save([])

    # Emulate a fresh load
    with patch(
        "homeassistant.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        hass.data.pop(DATA_RESTORE_STATE)
        await async_load(hass)
        data = async_get(hass)

        entity = RestoreEntity()
        entity.hass = hass
        entity.entity_id = "input_boolean.b1"

        await entity.async_get_last_state()
        await hass.async_block_till_done()

    # Startup Save
    expect(mock_write_data.called).to_be_truthy()

    with patch(
        "homeassistant.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=10))
        await hass.async_block_till_done()

    # Not quite the first interval
    expect(mock_write_data.called).to_be_falsy()

    with patch(
        "homeassistant.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        await RestoreStateData.async_save_persistent_states(hass)
        await hass.async_block_till_done()

    expect(mock_write_data.called).to_be_truthy()

    with patch(
        "homeassistant.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=20))
        await hass.async_block_till_done()
    # Verify still saving
    expect(mock_write_data.called).to_be_truthy()

    with patch(
        "homeassistant.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
        await hass.async_block_till_done()
    # Verify normal shutdown
    expect(mock_write_data.called).to_be_truthy()


@test
async def hass_starting(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that we cache data."""
    hass.set_state(CoreState.starting)

    now = dt_util.utcnow()
    stored_states = [
        StoredState(State("input_boolean.b0", "on"), None, now),
        StoredState(State("input_boolean.b1", "on"), None, now),
        StoredState(State("input_boolean.b2", "on"), None, now),
    ]

    data = async_get(hass)
    await hass.async_block_till_done()
    await data.store.async_save([state.as_dict() for state in stored_states])

    # Emulate a fresh load
    hass.set_state(CoreState.not_running)
    hass.data.pop(DATA_RESTORE_STATE)
    await async_load(hass)
    data = async_get(hass)

    entity = RestoreEntity()
    entity.hass = hass
    entity.entity_id = "input_boolean.b1"

    all_states = hass.states.async_all()
    expect(len(all_states)).to_equal(0)
    hass.states.async_set("input_boolean.b1", "on")

    # Mock that only b1 is present this run
    with patch(
        "homeassistant.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        state = await entity.async_get_last_state()
        await hass.async_block_till_done()

    expect(state).not_.to_be_none()
    expect(state.entity_id).to_equal("input_boolean.b1")
    expect(state.state).to_equal("on")
    hass.states.async_remove("input_boolean.b1")

    # Assert that no data was written yet, since hass is still starting.
    expect(mock_write_data.called).to_be_falsy()

    # Finish hass startup
    with patch(
        "homeassistant.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
        await hass.async_block_till_done()

    # Assert that this session states were written
    expect(mock_write_data.called).to_be_truthy()


@test
async def dump_data(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that we cache data."""
    states = [
        State("input_boolean.b0", "on"),
        State("input_boolean.b1", "on"),
        State("input_boolean.b2", "on"),
        State("input_boolean.b5", "unavailable", {"restored": True}),
    ]

    platform = MockEntityPlatform(hass, domain="input_boolean")
    entity = Entity()
    entity.hass = hass
    entity.entity_id = "input_boolean.b0"
    await platform.async_add_entities([entity])

    entity = RestoreEntity()
    entity.hass = hass
    entity.entity_id = "input_boolean.b1"
    await platform.async_add_entities([entity])

    data = async_get(hass)
    now = dt_util.utcnow()
    data.last_states = {
        "input_boolean.b0": StoredState(State("input_boolean.b0", "off"), None, now),
        "input_boolean.b1": StoredState(State("input_boolean.b1", "off"), None, now),
        "input_boolean.b2": StoredState(State("input_boolean.b2", "off"), None, now),
        "input_boolean.b3": StoredState(State("input_boolean.b3", "off"), None, now),
        "input_boolean.b4": StoredState(
            State("input_boolean.b4", "off"),
            None,
            datetime(1985, 10, 26, 1, 22, tzinfo=dt_util.UTC),
        ),
        "input_boolean.b5": StoredState(State("input_boolean.b5", "off"), None, now),
    }

    for state in states:
        hass.states.async_set(state.entity_id, state.state, state.attributes)

    with patch(
        "homeassistant.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        await data.async_dump_states()

    expect(mock_write_data.called).to_be_truthy()
    args = mock_write_data.mock_calls[0][1]
    written_states = args[0]

    for state in states:
        hass.states.async_remove(state.entity_id)
    # b0 should not be written, since it didn't extend RestoreEntity
    # b1 should be written, since it is present in the current run
    # b2 should not be written, since it is not registered with the helper
    # b3 should be written, since it is still not expired
    # b4 should not be written, since it is now expired
    # b5 should be written, since current state is restored by entity registry
    expect(len(written_states)).to_equal(3)
    state0 = json_round_trip(written_states[0])
    state1 = json_round_trip(written_states[1])
    state2 = json_round_trip(written_states[2])
    expect(state0["state"]["entity_id"]).to_equal("input_boolean.b1")
    expect(state0["state"]["state"]).to_equal("on")
    expect(state1["state"]["entity_id"]).to_equal("input_boolean.b3")
    expect(state1["state"]["state"]).to_equal("off")
    expect(state2["state"]["entity_id"]).to_equal("input_boolean.b5")
    expect(state2["state"]["state"]).to_equal("off")

    # Test that removed entities are not persisted
    await entity.async_remove()

    for state in states:
        hass.states.async_set(state.entity_id, state.state, state.attributes)

    with patch(
        "homeassistant.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        await data.async_dump_states()

    expect(mock_write_data.called).to_be_truthy()
    args = mock_write_data.mock_calls[0][1]
    written_states = args[0]
    expect(len(written_states)).to_equal(2)
    state0 = json_round_trip(written_states[0])
    state1 = json_round_trip(written_states[1])
    expect(state0["state"]["entity_id"]).to_equal("input_boolean.b3")
    expect(state0["state"]["state"]).to_equal("off")
    expect(state1["state"]["entity_id"]).to_equal("input_boolean.b5")
    expect(state1["state"]["state"]).to_equal("off")


@test.cases(
    test.case("home_assistant_error", exception=HomeAssistantError),
    test.case("runtime_error", exception=RuntimeError),
)
async def dump_error(
    exception: type[Exception],
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test that errors during save are caught."""
    states = [
        State("input_boolean.b0", "on"),
        State("input_boolean.b1", "on"),
        State("input_boolean.b2", "on"),
    ]

    platform = MockEntityPlatform(hass, domain="input_boolean")
    entity = Entity()
    entity.hass = hass
    entity.entity_id = "input_boolean.b0"
    await platform.async_add_entities([entity])

    entity = RestoreEntity()
    entity.hass = hass
    entity.entity_id = "input_boolean.b1"
    await platform.async_add_entities([entity])

    data = async_get(hass)

    for state in states:
        hass.states.async_set(state.entity_id, state.state, state.attributes)

    with patch(
        "homeassistant.helpers.restore_state.Store.async_save",
        side_effect=exception,
    ) as mock_write_data:
        await data.async_dump_states()

    expect(mock_write_data.called).to_be_truthy()


@test
async def load_error(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that we cache data."""
    entity = RestoreEntity()
    entity.hass = hass
    entity.entity_id = "input_boolean.b1"

    with patch(
        "homeassistant.helpers.storage.Store.async_load",
        side_effect=HomeAssistantError,
    ):
        state = await entity.async_get_last_state()

    expect(state).to_be_none()


@test
async def state_saved_on_remove(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that we save entity state on removal."""
    platform = MockEntityPlatform(hass, domain="input_boolean")
    entity = RestoreEntity()
    entity.hass = hass
    entity.entity_id = "input_boolean.b0"
    await platform.async_add_entities([entity])

    now = dt_util.utcnow()
    hass.states.async_set(
        "input_boolean.b0", "on", {"complicated": {"value": {1, 2, now}}}
    )

    data = async_get(hass)

    # No last states should currently be saved
    expect(data.last_states).to_be_falsy()

    await entity.async_remove()

    # We should store the input boolean state when it is removed
    state = data.last_states["input_boolean.b0"].state
    expect(state.state).to_equal("on")
    expect(isinstance(state.attributes["complicated"]["value"], list)).to_be_truthy()
    expect(set(state.attributes["complicated"]["value"])).to_equal(
        {1, 2, now.isoformat()}
    )


@test
async def restoring_invalid_entity_id(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test restoring invalid entity IDs."""
    entity = RestoreEntity()
    entity.hass = hass
    entity.entity_id = "test.invalid__entity_id"
    now = dt_util.utcnow().isoformat()
    hass_storage[STORAGE_KEY] = {
        "version": 1,
        "key": STORAGE_KEY,
        "data": [
            {
                "state": {
                    "entity_id": "test.invalid__entity_id",
                    "state": "off",
                    "attributes": {},
                    "last_changed": now,
                    "last_updated": now,
                    "context": {
                        "id": "3c2243ff5f30447eb12e7348cfd5b8ff",
                        "user_id": None,
                    },
                },
                "last_seen": dt_util.utcnow().isoformat(),
            }
        ],
    }

    state = await entity.async_get_last_state()
    expect(state).to_be_none()


@test
async def restore_entity_end_to_end(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test restoring an entity end-to-end."""
    component_setup = Mock(return_value=True)

    setup_called = []

    entity_id = "test_domain.unnamed_device"
    data = async_get(hass)
    now = dt_util.utcnow()
    data.last_states = {
        entity_id: StoredState(State(entity_id, "stored"), None, now),
    }

    class MockRestoreEntity(RestoreEntity):
        """Mock restore entity."""

        def __init__(self) -> None:
            """Initialize the mock entity."""
            self._state: str | None = None

        @property
        def state(self) -> str | None:
            """Return the state."""
            return self._state

        async def async_added_to_hass(self) -> Coroutine[Any, Any, None]:
            """Run when entity about to be added to hass."""
            await super().async_added_to_hass()
            self._state = (await self.async_get_last_state()).state

    async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> None:
        """Set up the test platform."""
        async_add_entities([MockRestoreEntity()])
        setup_called.append(True)

    mock_integration(hass, MockModule(DOMAIN, setup=component_setup))
    mock_integration(hass, MockModule(PLATFORM, dependencies=[DOMAIN]))

    platform = MockPlatform(async_setup_platform=async_setup_platform)
    mock_platform(hass, f"{PLATFORM}.{DOMAIN}", platform)

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    await component.async_setup({DOMAIN: {"platform": PLATFORM, "sensors": None}})
    await hass.async_block_till_done()
    expect(component_setup.called).to_be_truthy()

    expect(hass.config.components).to_contain(f"{PLATFORM}.{DOMAIN}")
    expect(len(setup_called)).to_equal(1)

    platform = async_get_platform_without_config_entry(hass, PLATFORM, DOMAIN)
    expect(platform.platform_name).to_equal(PLATFORM)
    expect(platform.domain).to_equal(DOMAIN)
    expect(hass.states.get(entity_id).state).to_equal("stored")

    await data.async_dump_states()
    await hass.async_block_till_done()

    storage_data = hass_storage[STORAGE_KEY]["data"]
    expect(len(storage_data)).to_equal(1)
    expect(storage_data[0]["state"]["entity_id"]).to_equal(entity_id)
    expect(storage_data[0]["state"]["state"]).to_equal("stored")

    await platform.async_reset()

    expect(hass.states.get(entity_id)).to_be_none()

    # Make sure the entity still gets saved to restore state
    # even though the platform has been reset since it should
    # not be expired yet.
    await data.async_dump_states()
    await hass.async_block_till_done()

    storage_data = hass_storage[STORAGE_KEY]["data"]
    expect(len(storage_data)).to_equal(1)
    expect(storage_data[0]["state"]["entity_id"]).to_equal(entity_id)
    expect(storage_data[0]["state"]["state"]).to_equal("stored")


@test
async def dump_states_with_failing_extra_data(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test that a failing extra_restore_state_data skips only that entity."""

    class BadRestoreEntity(RestoreEntity):
        """Entity that raises on extra_restore_state_data."""

        @property
        def extra_restore_state_data(self) -> ExtraStoredData | None:
            raise RuntimeError("Unexpected error")

    states = [
        State("input_boolean.good", "on"),
        State("input_boolean.bad", "on"),
    ]

    platform = MockEntityPlatform(hass, domain="input_boolean")

    good_entity = RestoreEntity()
    good_entity.hass = hass
    good_entity.entity_id = "input_boolean.good"
    await platform.async_add_entities([good_entity])

    bad_entity = BadRestoreEntity()
    bad_entity.hass = hass
    bad_entity.entity_id = "input_boolean.bad"
    await platform.async_add_entities([bad_entity])

    for state in states:
        hass.states.async_set(state.entity_id, state.state, state.attributes)

    data = async_get(hass)

    with patch(
        "homeassistant.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        await data.async_dump_states()

    expect(mock_write_data.called).to_be_truthy()
    written_states = mock_write_data.mock_calls[0][1][0]

    # Only the good entity should be saved
    expect(len(written_states)).to_equal(1)
    state0 = json_round_trip(written_states[0])
    expect(state0["state"]["entity_id"]).to_equal("input_boolean.good")
    expect(state0["state"]["state"]).to_equal("on")

    expect(caplog.text).to_contain(
        "Error getting extra restore state data for input_boolean.bad"
    )


@test
async def entity_removal_with_failing_extra_data(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test that entity removal succeeds even if extra_restore_state_data raises."""

    class BadRestoreEntity(RestoreEntity):
        """Entity that raises on extra_restore_state_data."""

        @property
        def extra_restore_state_data(self) -> ExtraStoredData | None:
            raise RuntimeError("Unexpected error")

    platform = MockEntityPlatform(hass, domain="input_boolean")
    entity = BadRestoreEntity()
    entity.hass = hass
    entity.entity_id = "input_boolean.bad"
    await platform.async_add_entities([entity])

    hass.states.async_set("input_boolean.bad", "on")

    data = async_get(hass)
    expect(data.entities).to_contain("input_boolean.bad")

    await entity.async_remove()

    # Entity should be unregistered
    expect(data.entities).not_.to_contain("input_boolean.bad")
    # No last state should be saved since extra data failed
    expect(data.last_states).not_.to_contain("input_boolean.bad")

    expect(caplog.text).to_contain(
        "Error getting extra restore state data for input_boolean.bad"
    )
