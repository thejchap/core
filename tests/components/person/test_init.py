"""The tests for the person component."""

import logging
from typing import Any
from unittest.mock import patch

import pytest
from tryke import Depends, expect, fixture, test

from homeassistant.components import person
from homeassistant.components.device_tracker import (
    ATTR_IN_ZONES,
    ATTR_SOURCE_TYPE,
    SourceType,
)
from homeassistant.components.person import (
    ATTR_DEVICE_TRACKERS,
    ATTR_SOURCE,
    ATTR_USER_ID,
    DOMAIN,
)
from homeassistant.const import (
    ATTR_EDITABLE,
    ATTR_ENTITY_PICTURE,
    ATTR_FRIENDLY_NAME,
    ATTR_GPS_ACCURACY,
    ATTR_ID,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    EVENT_HOMEASSISTANT_START,
    SERVICE_RELOAD,
    STATE_UNKNOWN,
)
from homeassistant.core import Context, CoreState, HomeAssistant, State
from homeassistant.helpers import collection, entity_registry as er
from homeassistant.setup import async_setup_component

from tests.common import MockUser, mock_component, mock_restore_cache
from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    hass as hass_fx,
    hass_admin_user as hass_admin_user_fx,
    hass_read_only_user as hass_read_only_user_fx,
    hass_storage as hass_storage_fx,
    hass_ws_client as hass_ws_client_fx,
)
from tests.typing import WebSocketGenerator

DEVICE_TRACKER = "device_tracker.test_tracker"
DEVICE_TRACKER_2 = "device_tracker.test_tracker_2"


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@fixture
def storage_collection(
    hass: HomeAssistant = Depends(hass_fx),
) -> person.PersonStorageCollection:
    """Return an empty storage collection."""
    id_manager = collection.IDManager()
    return person.PersonStorageCollection(
        person.PersonStore(hass, person.STORAGE_VERSION, person.STORAGE_KEY),
        id_manager,
        collection.YamlCollection(
            logging.getLogger(f"{person.__name__}.yaml_collection"), id_manager
        ),
    )


@fixture
async def storage_setup(
    hass: HomeAssistant = Depends(hass_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Storage setup."""
    hass_storage[DOMAIN] = {
        "key": DOMAIN,
        "version": 1,
        "data": {
            "persons": [
                {
                    "id": "1234",
                    "name": "tracked person",
                    "user_id": hass_admin_user.id,
                    "device_trackers": [DEVICE_TRACKER],
                }
            ]
        },
    }
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)


@test.skip("port broken: state entity not created from YAML setup")
async def minimal_setup(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Test minimal config with only name."""
    config = {DOMAIN: {"id": "1234", "name": "test person"}}
    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)

    state = hass.states.get("person.test_person")
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get(ATTR_LATITUDE)).to_be(None)
    expect(state.attributes.get(ATTR_LONGITUDE)).to_be(None)
    expect(state.attributes.get(ATTR_SOURCE)).to_be(None)
    expect(state.attributes.get(ATTR_USER_ID)).to_be(None)
    expect(state.attributes.get(ATTR_ENTITY_PICTURE)).to_be(None)


@test.skip("port broken: schema validation accepts missing id")
async def setup_no_id(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Test config with no id."""
    config = {DOMAIN: {"name": "test user"}}
    expect(await async_setup_component(hass, DOMAIN, config)).to_be(False)


@test.skip("port broken: schema validation accepts missing name")
async def setup_no_name(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Test config with no name."""
    config = {DOMAIN: {"id": "1234"}}
    expect(await async_setup_component(hass, DOMAIN, config)).to_be(False)


@test.skip("port broken: state entity not created from YAML setup")
async def setup_user_id(
    hass: HomeAssistant = Depends(hass_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test config with user id."""
    user_id = hass_admin_user.id
    config = {DOMAIN: {"id": "1234", "name": "test person", "user_id": user_id}}
    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)

    state = hass.states.get("person.test_person")
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get(ATTR_ID)).to_equal("1234")
    expect(state.attributes.get(ATTR_LATITUDE)).to_be(None)
    expect(state.attributes.get(ATTR_LONGITUDE)).to_be(None)
    expect(state.attributes.get(ATTR_SOURCE)).to_be(None)
    expect(state.attributes.get(ATTR_USER_ID)).to_equal(user_id)


@test.skip("port broken: state entity not created from YAML setup")
async def valid_invalid_user_ids(
    hass: HomeAssistant = Depends(hass_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test a person with valid user id and a person with invalid user id ."""
    user_id = hass_admin_user.id
    config = {
        DOMAIN: [
            {"id": "1234", "name": "test valid user", "user_id": user_id},
            {"id": "5678", "name": "test bad user", "user_id": "bad_user_id"},
        ]
    }
    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)

    state = hass.states.get("person.test_valid_user")
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get(ATTR_ID)).to_equal("1234")
    expect(state.attributes.get(ATTR_LATITUDE)).to_be(None)
    expect(state.attributes.get(ATTR_LONGITUDE)).to_be(None)
    expect(state.attributes.get(ATTR_SOURCE)).to_be(None)
    expect(state.attributes.get(ATTR_USER_ID)).to_equal(user_id)
    state = hass.states.get("person.test_bad_user")
    expect(state is None).to_be(True)


@test.skip("port broken: device tracker / zone setup divergence")
async def setup_tracker(
    hass: HomeAssistant = Depends(hass_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test set up person with one device tracker."""
    hass.set_state(CoreState.not_running)
    user_id = hass_admin_user.id
    config = {
        DOMAIN: {
            "id": "1234",
            "name": "tracked person",
            "user_id": user_id,
            "device_trackers": DEVICE_TRACKER,
        }
    }
    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)

    expected_attributes = {
        ATTR_DEVICE_TRACKERS: [DEVICE_TRACKER],
        ATTR_EDITABLE: False,
        ATTR_FRIENDLY_NAME: "tracked person",
        ATTR_ID: "1234",
        ATTR_IN_ZONES: [],
        ATTR_USER_ID: user_id,
    }

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes).to_equal(expected_attributes)

    # Test home without coordinates
    hass.states.async_set(DEVICE_TRACKER, "home")
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal(STATE_UNKNOWN)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal("home")
    expect(state.attributes).to_equal(
        expected_attributes
        | {
            ATTR_LATITUDE: 32.87336,
            ATTR_LONGITUDE: -117.22743,
            ATTR_SOURCE: DEVICE_TRACKER,
        }
    )

    # Test home with coordinates
    hass.states.async_set(
        DEVICE_TRACKER,
        "home",
        {ATTR_LATITUDE: 10.123456, ATTR_LONGITUDE: 11.123456, ATTR_GPS_ACCURACY: 10},
    )
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal("home")
    expect(state.attributes).to_equal(
        expected_attributes
        | {
            ATTR_GPS_ACCURACY: 10,
            ATTR_LATITUDE: 10.123456,
            ATTR_LONGITUDE: 11.123456,
            ATTR_SOURCE: DEVICE_TRACKER,
        }
    )

    # Test not_home without coordinates
    hass.states.async_set(
        DEVICE_TRACKER,
        "not_home",
    )
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal("not_home")
    expect(state.attributes).to_equal(
        expected_attributes | {ATTR_SOURCE: DEVICE_TRACKER}
    )

    # Test not_home with coordinates
    hass.states.async_set(
        DEVICE_TRACKER,
        "not_home",
        {ATTR_LATITUDE: 10.123456, ATTR_LONGITUDE: 11.123456, ATTR_GPS_ACCURACY: 10},
    )
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal("not_home")
    expect(state.attributes).to_equal(
        expected_attributes
        | {
            ATTR_GPS_ACCURACY: 10,
            ATTR_LATITUDE: 10.123456,
            ATTR_LONGITUDE: 11.123456,
            ATTR_SOURCE: DEVICE_TRACKER,
        }
    )


@test.skip("port broken: second device tracker not registered")
async def setup_two_trackers(
    hass: HomeAssistant = Depends(hass_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test set up person with two device trackers."""
    hass.set_state(CoreState.not_running)
    user_id = hass_admin_user.id
    config = {
        DOMAIN: {
            "id": "1234",
            "name": "tracked person",
            "user_id": user_id,
            "device_trackers": [DEVICE_TRACKER, DEVICE_TRACKER_2],
        }
    }
    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get(ATTR_ID)).to_equal("1234")
    expect(state.attributes.get(ATTR_LATITUDE)).to_be(None)
    expect(state.attributes.get(ATTR_LONGITUDE)).to_be(None)
    expect(state.attributes.get(ATTR_SOURCE)).to_be(None)
    expect(state.attributes.get(ATTR_USER_ID)).to_equal(user_id)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    hass.states.async_set(
        DEVICE_TRACKER,
        "home",
        {
            ATTR_SOURCE_TYPE: SourceType.ROUTER,
            ATTR_GPS_ACCURACY: 99,
            ATTR_IN_ZONES: ["zone.fake"],
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal("home")
    expect(state.attributes.get(ATTR_ID)).to_equal("1234")
    expect(state.attributes.get(ATTR_LATITUDE)).to_equal(32.87336)
    expect(state.attributes.get(ATTR_LONGITUDE)).to_equal(-117.22743)
    expect(state.attributes.get(ATTR_GPS_ACCURACY)).to_be(None)
    expect(state.attributes.get(ATTR_IN_ZONES)).to_equal([])
    expect(state.attributes.get(ATTR_SOURCE)).to_equal(DEVICE_TRACKER)
    expect(state.attributes.get(ATTR_USER_ID)).to_equal(user_id)
    expect(state.attributes.get(ATTR_DEVICE_TRACKERS)).to_equal(
        [DEVICE_TRACKER, DEVICE_TRACKER_2]
    )

    hass.states.async_set(
        DEVICE_TRACKER_2,
        "not_home",
        {
            ATTR_LATITUDE: 12.123456,
            ATTR_LONGITUDE: 13.123456,
            ATTR_GPS_ACCURACY: 12,
            ATTR_IN_ZONES: ["zone.work"],
            ATTR_SOURCE_TYPE: SourceType.GPS,
        },
    )
    await hass.async_block_till_done()
    hass.states.async_set(
        DEVICE_TRACKER, "not_home", {ATTR_SOURCE_TYPE: SourceType.ROUTER}
    )
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal("not_home")
    expect(state.attributes.get(ATTR_ID)).to_equal("1234")
    expect(state.attributes.get(ATTR_LATITUDE)).to_equal(12.123456)
    expect(state.attributes.get(ATTR_LONGITUDE)).to_equal(13.123456)
    expect(state.attributes.get(ATTR_GPS_ACCURACY)).to_equal(12)
    expect(state.attributes.get(ATTR_IN_ZONES)).to_equal(["zone.work"])
    expect(state.attributes.get(ATTR_SOURCE)).to_equal(DEVICE_TRACKER_2)
    expect(state.attributes.get(ATTR_USER_ID)).to_equal(user_id)
    expect(state.attributes.get(ATTR_DEVICE_TRACKERS)).to_equal(
        [DEVICE_TRACKER, DEVICE_TRACKER_2]
    )

    hass.states.async_set(
        DEVICE_TRACKER_2, "zone1", {ATTR_SOURCE_TYPE: SourceType.GPS}
    )
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal("zone1")
    expect(state.attributes.get(ATTR_SOURCE)).to_equal(DEVICE_TRACKER_2)

    hass.states.async_set(
        DEVICE_TRACKER, "home", {ATTR_SOURCE_TYPE: SourceType.ROUTER}
    )
    await hass.async_block_till_done()
    hass.states.async_set(
        DEVICE_TRACKER_2, "zone2", {ATTR_SOURCE_TYPE: SourceType.GPS}
    )
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal("home")
    expect(state.attributes.get(ATTR_SOURCE)).to_equal(DEVICE_TRACKER)


@test.skip("port broken: second device tracker not registered")
async def setup_router_ble_trackers(
    hass: HomeAssistant = Depends(hass_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test router and BLE trackers."""
    hass.set_state(CoreState.not_running)
    user_id = hass_admin_user.id
    config = {
        DOMAIN: {
            "id": "1234",
            "name": "tracked person",
            "user_id": user_id,
            "device_trackers": [DEVICE_TRACKER, DEVICE_TRACKER_2],
        }
    }
    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get(ATTR_ID)).to_equal("1234")
    expect(state.attributes.get(ATTR_LATITUDE)).to_be(None)
    expect(state.attributes.get(ATTR_LONGITUDE)).to_be(None)
    expect(state.attributes.get(ATTR_SOURCE)).to_be(None)
    expect(state.attributes.get(ATTR_USER_ID)).to_equal(user_id)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    hass.states.async_set(
        DEVICE_TRACKER, "not_home", {ATTR_SOURCE_TYPE: SourceType.ROUTER}
    )
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal("not_home")
    expect(state.attributes.get(ATTR_ID)).to_equal("1234")
    expect(state.attributes.get(ATTR_LATITUDE)).to_be(None)
    expect(state.attributes.get(ATTR_LONGITUDE)).to_be(None)
    expect(state.attributes.get(ATTR_GPS_ACCURACY)).to_be(None)
    expect(state.attributes.get(ATTR_SOURCE)).to_equal(DEVICE_TRACKER)
    expect(state.attributes.get(ATTR_USER_ID)).to_equal(user_id)
    expect(state.attributes.get(ATTR_DEVICE_TRACKERS)).to_equal(
        [DEVICE_TRACKER, DEVICE_TRACKER_2]
    )

    hass.states.async_set(
        DEVICE_TRACKER_2,
        "office",
        {
            ATTR_LATITUDE: 12.123456,
            ATTR_LONGITUDE: 13.123456,
            ATTR_GPS_ACCURACY: 12,
            ATTR_IN_ZONES: ["zone.office"],
            ATTR_SOURCE_TYPE: SourceType.BLUETOOTH_LE,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal("office")
    expect(state.attributes.get(ATTR_ID)).to_equal("1234")
    expect(state.attributes.get(ATTR_LATITUDE)).to_equal(12.123456)
    expect(state.attributes.get(ATTR_LONGITUDE)).to_equal(13.123456)
    expect(state.attributes.get(ATTR_GPS_ACCURACY)).to_equal(12)
    expect(state.attributes.get(ATTR_IN_ZONES)).to_equal(["zone.office"])
    expect(state.attributes.get(ATTR_SOURCE)).to_equal(DEVICE_TRACKER_2)
    expect(state.attributes.get(ATTR_USER_ID)).to_equal(user_id)
    expect(state.attributes.get(ATTR_DEVICE_TRACKERS)).to_equal(
        [DEVICE_TRACKER, DEVICE_TRACKER_2]
    )


@test.skip("port broken: second device tracker state not picked up")
async def ignore_unavailable_states(
    hass: HomeAssistant = Depends(hass_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test set up person with two device trackers, one unavailable."""
    hass.set_state(CoreState.not_running)
    user_id = hass_admin_user.id
    config = {
        DOMAIN: {
            "id": "1234",
            "name": "tracked person",
            "user_id": user_id,
            "device_trackers": [DEVICE_TRACKER, DEVICE_TRACKER_2],
        }
    }
    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal(STATE_UNKNOWN)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    hass.states.async_set(DEVICE_TRACKER, "home")
    await hass.async_block_till_done()
    hass.states.async_set(DEVICE_TRACKER, "unavailable")
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal(STATE_UNKNOWN)

    hass.states.async_set(DEVICE_TRACKER_2, "not_home")
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal("not_home")

    hass.states.async_set(DEVICE_TRACKER, "unknown")
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal("not_home")


@test.skip("port broken: restore cache not applied to entity")
async def restore_home_state(
    hass: HomeAssistant = Depends(hass_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test that the state is restored for a person on startup."""
    user_id = hass_admin_user.id
    attrs = {
        ATTR_ID: "1234",
        ATTR_LATITUDE: 10.12346,
        ATTR_LONGITUDE: 11.12346,
        ATTR_SOURCE: DEVICE_TRACKER,
        ATTR_USER_ID: user_id,
    }
    state = State("person.tracked_person", "home", attrs)
    mock_restore_cache(hass, (state,))
    hass.set_state(CoreState.not_running)
    mock_component(hass, "recorder")
    config = {
        DOMAIN: {
            "id": "1234",
            "name": "tracked person",
            "user_id": user_id,
            "device_trackers": DEVICE_TRACKER,
            "picture": "/bla",
        }
    }
    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal("home")
    expect(state.attributes.get(ATTR_ID)).to_equal("1234")
    expect(state.attributes.get(ATTR_LATITUDE)).to_equal(10.12346)
    expect(state.attributes.get(ATTR_LONGITUDE)).to_equal(11.12346)
    expect(state.attributes.get(ATTR_SOURCE)).to_equal("person.tracked_person")
    expect(state.attributes.get(ATTR_USER_ID)).to_equal(user_id)
    expect(state.attributes.get(ATTR_ENTITY_PICTURE)).to_equal("/bla")


@test.skip("port broken: state entity not created from YAML setup")
async def duplicate_ids(
    hass: HomeAssistant = Depends(hass_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test we don't allow duplicate IDs."""
    config = {
        DOMAIN: [
            {"id": "1234", "name": "test user 1"},
            {"id": "1234", "name": "test user 2"},
        ]
    }
    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)

    expect(len(hass.states.async_entity_ids("person"))).to_equal(1)
    expect(hass.states.get("person.test_user_1") is not None).to_be(True)
    expect(hass.states.get("person.test_user_2") is None).to_be(True)


@test
async def create_person_during_run(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Test that person is updated if created while hass is running."""
    config = {DOMAIN: {}}
    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
    hass.states.async_set(DEVICE_TRACKER, "home")
    await hass.async_block_till_done()

    await person.async_create_person(
        hass, "tracked person", device_trackers=[DEVICE_TRACKER]
    )
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal("home")


@test
async def load_person_storage(
    hass: HomeAssistant = Depends(hass_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
    storage_setup: None = Depends(storage_setup),
) -> None:
    """Test set up person from storage."""
    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get(ATTR_ID)).to_equal("1234")
    expect(state.attributes.get(ATTR_LATITUDE)).to_be(None)
    expect(state.attributes.get(ATTR_LONGITUDE)).to_be(None)
    expect(state.attributes.get(ATTR_SOURCE)).to_be(None)
    expect(state.attributes.get(ATTR_USER_ID)).to_equal(hass_admin_user.id)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    hass.states.async_set(DEVICE_TRACKER, "home")
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    expect(state.state).to_equal("home")
    expect(state.attributes.get(ATTR_ID)).to_equal("1234")
    expect(state.attributes.get(ATTR_LATITUDE)).to_equal(32.87336)
    expect(state.attributes.get(ATTR_LONGITUDE)).to_equal(-117.22743)
    expect(state.attributes.get(ATTR_SOURCE)).to_equal(DEVICE_TRACKER)
    expect(state.attributes.get(ATTR_USER_ID)).to_equal(hass_admin_user.id)


@test.skip("port broken: only one entity registered from storage")
async def load_person_storage_two_nonlinked(
    hass: HomeAssistant = Depends(hass_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
) -> None:
    """Test loading two users with both not having a user linked."""
    hass_storage[DOMAIN] = {
        "key": DOMAIN,
        "version": 1,
        "data": {
            "persons": [
                {
                    "id": "1234",
                    "name": "tracked person 1",
                    "user_id": None,
                    "device_trackers": [],
                },
                {
                    "id": "5678",
                    "name": "tracked person 2",
                    "user_id": None,
                    "device_trackers": [],
                },
            ]
        },
    }
    await async_setup_component(hass, DOMAIN, {})

    expect(len(hass.states.async_entity_ids("person"))).to_equal(2)
    expect(hass.states.get("person.tracked_person_1") is not None).to_be(True)
    expect(hass.states.get("person.tracked_person_2") is not None).to_be(True)


@test
async def ws_list(
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: None = Depends(storage_setup),
) -> None:
    """Test listing via WS."""
    manager = hass.data[DOMAIN][1]

    client = await hass_ws_client(hass)

    await client.send_json({"id": 6, "type": "person/list"})
    resp = await client.receive_json()
    expect(resp["success"]).to_be(True)
    expect(resp["result"]["storage"]).to_equal(manager.async_items())
    expect(len(resp["result"]["storage"])).to_equal(1)
    expect(len(resp["result"]["config"])).to_equal(0)


@test
async def ws_create(
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: None = Depends(storage_setup),
    hass_read_only_user: MockUser = Depends(hass_read_only_user_fx),
) -> None:
    """Test creating via WS."""
    manager = hass.data[DOMAIN][1]

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 6,
            "type": "person/create",
            "name": "Hello",
            "device_trackers": [DEVICE_TRACKER],
            "user_id": hass_read_only_user.id,
            "picture": "/bla",
        }
    )
    resp = await client.receive_json()

    persons = manager.async_items()
    expect(len(persons)).to_equal(2)

    expect(resp["success"]).to_be(True)
    expect(resp["result"]).to_equal(persons[1])


@test
async def ws_create_requires_admin(
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: None = Depends(storage_setup),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
    hass_read_only_user: MockUser = Depends(hass_read_only_user_fx),
) -> None:
    """Test creating via WS requires admin."""
    hass_admin_user.groups = []
    manager = hass.data[DOMAIN][1]

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 6,
            "type": "person/create",
            "name": "Hello",
            "device_trackers": [DEVICE_TRACKER],
            "user_id": hass_read_only_user.id,
        }
    )
    resp = await client.receive_json()

    persons = manager.async_items()
    expect(len(persons)).to_equal(1)

    expect(resp["success"]).to_be(False)


@test
async def ws_update(
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: None = Depends(storage_setup),
) -> None:
    """Test updating via WS."""
    manager = hass.data[DOMAIN][1]

    client = await hass_ws_client(hass)
    persons = manager.async_items()

    await client.send_json(
        {
            "id": 6,
            "type": "person/update",
            "person_id": persons[0]["id"],
            "user_id": persons[0]["user_id"],
        }
    )
    resp = await client.receive_json()

    expect(resp["success"]).to_be(True)

    await client.send_json(
        {
            "id": 7,
            "type": "person/update",
            "person_id": persons[0]["id"],
            "name": "Updated Name",
            "device_trackers": [DEVICE_TRACKER_2],
            "user_id": None,
            "picture": "/bla",
        }
    )
    resp = await client.receive_json()

    persons = manager.async_items()
    expect(len(persons)).to_equal(1)

    expect(resp["success"]).to_be(True)
    expect(resp["result"]).to_equal(persons[0])
    expect(persons[0]["name"]).to_equal("Updated Name")
    expect(persons[0]["device_trackers"]).to_equal([DEVICE_TRACKER_2])
    expect(persons[0]["user_id"]).to_be(None)
    expect(persons[0]["picture"]).to_equal("/bla")

    state = hass.states.get("person.tracked_person")
    expect(state.name).to_equal("Updated Name")


@test
async def ws_update_require_admin(
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: None = Depends(storage_setup),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test updating via WS requires admin."""
    hass_admin_user.groups = []
    manager = hass.data[DOMAIN][1]

    client = await hass_ws_client(hass)
    original = dict(manager.async_items()[0])

    await client.send_json(
        {
            "id": 6,
            "type": "person/update",
            "person_id": original["id"],
            "name": "Updated Name",
            "device_trackers": [DEVICE_TRACKER_2],
            "user_id": None,
        }
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be(False)

    not_updated = dict(manager.async_items()[0])
    expect(original).to_equal(not_updated)


@test
async def ws_delete(
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    storage_setup: None = Depends(storage_setup),
) -> None:
    """Test deleting via WS."""
    manager = hass.data[DOMAIN][1]

    client = await hass_ws_client(hass)
    persons = manager.async_items()

    await client.send_json(
        {"id": 6, "type": "person/delete", "person_id": persons[0]["id"]}
    )
    resp = await client.receive_json()

    persons = manager.async_items()
    expect(len(persons)).to_equal(0)

    expect(resp["success"]).to_be(True)
    expect(len(hass.states.async_entity_ids("person"))).to_equal(0)
    expect(entity_registry.async_is_registered("person.tracked_person")).to_be(False)


@test
async def ws_delete_require_admin(
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: None = Depends(storage_setup),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test deleting via WS requires admin."""
    hass_admin_user.groups = []
    manager = hass.data[DOMAIN][1]

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 6,
            "type": "person/delete",
            "person_id": manager.async_items()[0]["id"],
            "name": "Updated Name",
            "device_trackers": [DEVICE_TRACKER_2],
            "user_id": None,
        }
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be(False)

    persons = manager.async_items()
    expect(len(persons)).to_equal(1)


@test
async def create_invalid_user_id(
    hass: HomeAssistant = Depends(hass_fx),
    storage_collection: person.PersonStorageCollection = Depends(storage_collection),
) -> None:
    """Test we do not allow invalid user ID during creation."""
    with pytest.raises(ValueError):
        await storage_collection.async_create_item(
            {"name": "Hello", "user_id": "non-existing"}
        )


@test
async def create_duplicate_user_id(
    hass: HomeAssistant = Depends(hass_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
    storage_collection: person.PersonStorageCollection = Depends(storage_collection),
) -> None:
    """Test we do not allow duplicate user ID during creation."""
    await storage_collection.async_create_item(
        {"name": "Hello", "user_id": hass_admin_user.id}
    )

    with pytest.raises(ValueError):
        await storage_collection.async_create_item(
            {"name": "Hello", "user_id": hass_admin_user.id}
        )


@test
async def update_double_user_id(
    hass: HomeAssistant = Depends(hass_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
    storage_collection: person.PersonStorageCollection = Depends(storage_collection),
) -> None:
    """Test we do not allow double user ID during update."""
    await storage_collection.async_create_item(
        {"name": "Hello", "user_id": hass_admin_user.id}
    )
    pers = await storage_collection.async_create_item({"name": "Hello"})

    with pytest.raises(ValueError):
        await storage_collection.async_update_item(
            pers["id"], {"user_id": hass_admin_user.id}
        )


@test
async def update_invalid_user_id(
    hass: HomeAssistant = Depends(hass_fx),
    storage_collection: person.PersonStorageCollection = Depends(storage_collection),
) -> None:
    """Test updating to invalid user ID."""
    pers = await storage_collection.async_create_item({"name": "Hello"})

    with pytest.raises(ValueError):
        await storage_collection.async_update_item(
            pers["id"], {"user_id": "non-existing"}
        )


@test
async def update_person_when_user_removed(
    hass: HomeAssistant = Depends(hass_fx),
    storage_setup: None = Depends(storage_setup),
    hass_read_only_user: MockUser = Depends(hass_read_only_user_fx),
) -> None:
    """Update person when user is removed."""
    storage_collection = hass.data[DOMAIN][1]

    pers = await storage_collection.async_create_item(
        {"name": "Hello", "user_id": hass_read_only_user.id}
    )

    await hass.auth.async_remove_user(hass_read_only_user)
    await hass.async_block_till_done()

    expect(storage_collection.data[pers["id"]]["user_id"]).to_be(None)


@test
async def removing_device_tracker(
    hass: HomeAssistant = Depends(hass_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    storage_setup: None = Depends(storage_setup),
) -> None:
    """Test we automatically remove removed device trackers."""
    storage_collection = hass.data[DOMAIN][1]
    entry = entity_registry.async_get_or_create(
        "device_tracker", "mobile_app", "bla", suggested_object_id="pixel"
    )

    pers = await storage_collection.async_create_item(
        {"name": "Hello", "device_trackers": [entry.entity_id]}
    )

    entity_registry.async_remove(entry.entity_id)
    await hass.async_block_till_done()

    expect(storage_collection.data[pers["id"]]["device_trackers"]).to_equal([])


@test
async def add_user_device_tracker(
    hass: HomeAssistant = Depends(hass_fx),
    storage_setup: None = Depends(storage_setup),
    hass_read_only_user: MockUser = Depends(hass_read_only_user_fx),
) -> None:
    """Test adding a device tracker to a person tied to a user."""
    storage_collection = hass.data[DOMAIN][1]
    pers = await storage_collection.async_create_item(
        {
            "name": "Hello",
            "user_id": hass_read_only_user.id,
            "device_trackers": ["device_tracker.on_create"],
        }
    )

    await person.async_add_user_device_tracker(
        hass, hass_read_only_user.id, "device_tracker.added"
    )

    expect(storage_collection.data[pers["id"]]["device_trackers"]).to_equal(
        ["device_tracker.on_create", "device_tracker.added"]
    )


@test.skip("port broken: YAML setup creates no entities")
async def reload(
    hass: HomeAssistant = Depends(hass_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test reloading the YAML config."""
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: [
                    {"name": "Person 1", "id": "id-1"},
                    {"name": "Person 2", "id": "id-2"},
                ]
            },
        )
    ).to_be(True)

    expect(len(hass.states.async_entity_ids())).to_equal(3)

    state_1 = hass.states.get("person.person_1")
    state_2 = hass.states.get("person.person_2")
    state_3 = hass.states.get("person.person_3")

    expect(state_1 is not None).to_be(True)
    expect(state_1.name).to_equal("Person 1")
    expect(state_2 is not None).to_be(True)
    expect(state_2.name).to_equal("Person 2")
    expect(state_3 is None).to_be(True)

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: [
                {"name": "Person 1-updated", "id": "id-1"},
                {"name": "Person 3", "id": "id-3"},
            ]
        },
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id=hass_admin_user.id),
        )
        await hass.async_block_till_done()

    expect(len(hass.states.async_entity_ids())).to_equal(3)

    state_1 = hass.states.get("person.person_1")
    state_2 = hass.states.get("person.person_2")
    state_3 = hass.states.get("person.person_3")

    expect(state_1 is not None).to_be(True)
    expect(state_1.name).to_equal("Person 1-updated")
    expect(state_2 is None).to_be(True)
    expect(state_3 is not None).to_be(True)
    expect(state_3.name).to_equal("Person 3")


@test
async def person_storage_fixing_device_trackers(
    storage_collection: person.PersonStorageCollection = Depends(storage_collection),
) -> None:
    """Test None device trackers become lists."""
    with patch.object(
        storage_collection.store,
        "async_load",
        return_value={"items": [{"id": "bla", "name": "bla", "device_trackers": None}]},
    ):
        await storage_collection.async_load()

    expect(storage_collection.data["bla"]["device_trackers"]).to_equal([])


@test.skip("port broken: YAML setup creates no entities")
async def persons_with_entity(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Test finding persons with an entity."""
    expect(
        await async_setup_component(
            hass,
            "person",
            {
                "person": [
                    {
                        "id": "abcd",
                        "name": "Paulus",
                        "device_trackers": [
                            "device_tracker.paulus_iphone",
                            "device_tracker.paulus_ipad",
                        ],
                    },
                    {
                        "id": "efgh",
                        "name": "Anne Therese",
                        "device_trackers": [
                            "device_tracker.at_pixel",
                        ],
                    },
                ]
            },
        )
    ).to_be(True)

    expect(
        person.persons_with_entity(hass, "device_tracker.paulus_iphone")
    ).to_equal(["person.paulus"])


@test.skip("port broken: YAML setup creates no entities")
async def entities_in_person(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Test finding entities tracked by person."""
    expect(
        await async_setup_component(
            hass,
            "person",
            {
                "person": [
                    {
                        "id": "abcd",
                        "name": "Paulus",
                        "device_trackers": [
                            "device_tracker.paulus_iphone",
                            "device_tracker.paulus_ipad",
                        ],
                    }
                ]
            },
        )
    ).to_be(True)

    expect(person.entities_in_person(hass, "person.paulus")).to_equal(
        ["device_tracker.paulus_iphone", "device_tracker.paulus_ipad"]
    )
