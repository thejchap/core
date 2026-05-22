"""Tests for the Input slider component."""

import datetime
from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import patch

import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant.components.input_datetime import (
    ATTR_DATE,
    ATTR_DATETIME,
    ATTR_EDITABLE,
    ATTR_TIME,
    ATTR_TIMESTAMP,
    CONF_HAS_DATE,
    CONF_HAS_TIME,
    CONF_INITIAL,
    CONF_NAME,
    CONFIG_SCHEMA,
    DEFAULT_TIME,
    DOMAIN,
    SERVICE_RELOAD,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_NAME,
    FORMAT_DATE,
    FORMAT_DATETIME,
    FORMAT_TIME,
)
from homeassistant.core import Context, CoreState, HomeAssistant, State
from homeassistant.exceptions import Unauthorized
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from ._fixtures import storage_setup as storage_setup_fx

from tests.common import MockUser, mock_restore_cache
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fx,
    hass_read_only_user as hass_read_only_user_fx,
    hass_ws_client as hass_ws_client_fx,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.typing import WebSocketGenerator

INITIAL_DATE = "2020-01-10"
INITIAL_TIME = "23:45:56"
INITIAL_DATETIME = f"{INITIAL_DATE} {INITIAL_TIME}"


@fixture
def _trigger_executor() -> int:
    return 0


async def async_set_date_and_time(
    hass: HomeAssistant, entity_id: str, dt_value: datetime.datetime
) -> None:
    """Set date and / or time of input_datetime."""
    await hass.services.async_call(
        DOMAIN,
        "set_datetime",
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_DATE: dt_value.date(),
            ATTR_TIME: dt_value.time(),
        },
        blocking=True,
    )


async def async_set_datetime(
    hass: HomeAssistant, entity_id: str, dt_value: datetime.datetime
) -> None:
    """Set date and / or time of input_datetime."""
    await hass.services.async_call(
        DOMAIN,
        "set_datetime",
        {ATTR_ENTITY_ID: entity_id, ATTR_DATETIME: dt_value},
        blocking=True,
    )


async def async_set_timestamp(
    hass: HomeAssistant, entity_id: str, timestamp: float
) -> None:
    """Set date and / or time of input_datetime."""
    await hass.services.async_call(
        DOMAIN,
        "set_datetime",
        {ATTR_ENTITY_ID: entity_id, ATTR_TIMESTAMP: timestamp},
        blocking=True,
    )


@test.cases(
    test.case("none", invalid_config=None),
    test.case("name_with_space", invalid_config={"name with space": None}),
    test.case(
        "no_value",
        invalid_config={"test_no_value": {"has_time": False, "has_date": False}},
    ),
)
async def invalid_configs(invalid_config: Any) -> None:
    """Test config."""
    expect(lambda: CONFIG_SCHEMA({DOMAIN: invalid_config})).to_raise(vol.Invalid)


@test
async def set_datetime(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test set_datetime method using date & time."""
    await async_setup_component(
        hass, DOMAIN, {DOMAIN: {"test_datetime": {"has_time": True, "has_date": True}}}
    )

    entity_id = "input_datetime.test_datetime"

    dt_obj = datetime.datetime(
        2017, 9, 7, 19, 46, 30, tzinfo=dt_util.get_time_zone(hass.config.time_zone)
    )

    await async_set_date_and_time(hass, entity_id, dt_obj)

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(dt_obj.strftime(FORMAT_DATETIME))
    expect(state.attributes["has_time"]).to_be(True)
    expect(state.attributes["has_date"]).to_be(True)

    expect(state.attributes["year"]).to_equal(2017)
    expect(state.attributes["month"]).to_equal(9)
    expect(state.attributes["day"]).to_equal(7)
    expect(state.attributes["hour"]).to_equal(19)
    expect(state.attributes["minute"]).to_equal(46)
    expect(state.attributes["second"]).to_equal(30)
    expect(state.attributes["timestamp"]).to_equal(dt_obj.timestamp())


@test
async def set_datetime_2(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test set_datetime method using datetime."""
    await async_setup_component(
        hass, DOMAIN, {DOMAIN: {"test_datetime": {"has_time": True, "has_date": True}}}
    )

    entity_id = "input_datetime.test_datetime"

    dt_obj = datetime.datetime(
        2017, 9, 7, 19, 46, 30, tzinfo=dt_util.get_time_zone(hass.config.time_zone)
    )

    await async_set_datetime(hass, entity_id, dt_obj)

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(dt_obj.strftime(FORMAT_DATETIME))
    expect(state.attributes["has_time"]).to_be(True)
    expect(state.attributes["has_date"]).to_be(True)

    expect(state.attributes["year"]).to_equal(2017)
    expect(state.attributes["month"]).to_equal(9)
    expect(state.attributes["day"]).to_equal(7)
    expect(state.attributes["hour"]).to_equal(19)
    expect(state.attributes["minute"]).to_equal(46)
    expect(state.attributes["second"]).to_equal(30)
    expect(state.attributes["timestamp"]).to_equal(dt_obj.timestamp())


@test
async def set_datetime_3(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test set_datetime method using timestamp."""
    await async_setup_component(
        hass, DOMAIN, {DOMAIN: {"test_datetime": {"has_time": True, "has_date": True}}}
    )

    entity_id = "input_datetime.test_datetime"

    dt_obj = datetime.datetime(
        2017, 9, 7, 19, 46, 30, tzinfo=dt_util.get_time_zone(hass.config.time_zone)
    )

    await async_set_timestamp(hass, entity_id, dt_util.as_utc(dt_obj).timestamp())

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(dt_obj.strftime(FORMAT_DATETIME))
    expect(state.attributes["has_time"]).to_be(True)
    expect(state.attributes["has_date"]).to_be(True)

    expect(state.attributes["year"]).to_equal(2017)
    expect(state.attributes["month"]).to_equal(9)
    expect(state.attributes["day"]).to_equal(7)
    expect(state.attributes["hour"]).to_equal(19)
    expect(state.attributes["minute"]).to_equal(46)
    expect(state.attributes["second"]).to_equal(30)
    expect(state.attributes["timestamp"]).to_equal(dt_obj.timestamp())


@test
async def set_datetime_4(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test set_datetime method using timestamp 0."""
    await async_setup_component(
        hass, DOMAIN, {DOMAIN: {"test_datetime": {"has_time": True, "has_date": True}}}
    )

    entity_id = "input_datetime.test_datetime"

    dt_obj = datetime.datetime(
        1969, 12, 31, 16, 00, 00, tzinfo=dt_util.get_time_zone(hass.config.time_zone)
    )

    await async_set_timestamp(hass, entity_id, 0)

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(dt_obj.strftime(FORMAT_DATETIME))
    expect(state.attributes["has_time"]).to_be(True)
    expect(state.attributes["has_date"]).to_be(True)

    expect(state.attributes["year"]).to_equal(1969)
    expect(state.attributes["month"]).to_equal(12)
    expect(state.attributes["day"]).to_equal(31)
    expect(state.attributes["hour"]).to_equal(16)
    expect(state.attributes["minute"]).to_equal(0)
    expect(state.attributes["second"]).to_equal(0)
    expect(state.attributes["timestamp"]).to_equal(0)


@test
async def set_datetime_time(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test set_datetime method with only time."""
    await async_setup_component(
        hass, DOMAIN, {DOMAIN: {"test_time": {"has_time": True, "has_date": False}}}
    )

    entity_id = "input_datetime.test_time"

    dt_obj = datetime.datetime(2017, 9, 7, 19, 46, 30)

    await async_set_date_and_time(hass, entity_id, dt_obj)

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(dt_obj.strftime(FORMAT_TIME))
    expect(state.attributes["has_time"]).to_be(True)
    expect(state.attributes["has_date"]).to_be(False)

    expect(state.attributes["timestamp"]).to_equal((19 * 3600) + (46 * 60) + 30)


@test
async def set_invalid(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test set_datetime method with only time."""
    initial = "2017-01-01"
    await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "test_date": {"has_time": False, "has_date": True, "initial": initial}
            }
        },
    )

    entity_id = "input_datetime.test_date"

    dt_obj = datetime.datetime(2017, 9, 7, 19, 46)
    time_portion = dt_obj.time()

    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(
            "input_datetime",
            "set_datetime",
            {"entity_id": entity_id, "time": time_portion},
            blocking=True,
        )

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(initial)


@test
async def set_invalid_2(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test set_datetime method with date and datetime."""
    initial = "2017-01-01"
    await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "test_date": {"has_time": False, "has_date": True, "initial": initial}
            }
        },
    )

    entity_id = "input_datetime.test_date"

    dt_obj = datetime.datetime(2017, 9, 7, 19, 46)
    time_portion = dt_obj.time()

    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(
            "input_datetime",
            "set_datetime",
            {"entity_id": entity_id, "time": time_portion, "datetime": dt_obj},
            blocking=True,
        )

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(initial)


@test
async def set_datetime_date(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test set_datetime method with only date."""
    await async_setup_component(
        hass, DOMAIN, {DOMAIN: {"test_date": {"has_time": False, "has_date": True}}}
    )

    entity_id = "input_datetime.test_date"

    dt_obj = datetime.datetime(2017, 9, 7, 19, 46)
    date_portion = dt_obj.date()

    await async_set_date_and_time(hass, entity_id, dt_obj)

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(str(date_portion))
    expect(state.attributes["has_time"]).to_be(False)
    expect(state.attributes["has_date"]).to_be(True)

    date_dt_obj = datetime.datetime(2017, 9, 7)
    expect(state.attributes["timestamp"]).to_equal(date_dt_obj.timestamp())


@test
async def restore_state(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Ensure states are restored on startup."""
    mock_restore_cache(
        hass,
        (
            State("input_datetime.test_time", "19:46:00"),
            State("input_datetime.test_date", "2017-09-07"),
            State("input_datetime.test_datetime", "2017-09-07 19:46:00"),
            State("input_datetime.test_bogus_data", "this is not a date"),
            State("input_datetime.test_was_time", "19:46:00"),
            State("input_datetime.test_was_date", "2017-09-07"),
        ),
    )

    hass.set_state(CoreState.starting)

    initial = datetime.datetime(2017, 1, 1, 23, 42)
    default = datetime.datetime.combine(datetime.date.today(), DEFAULT_TIME)

    await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "test_time": {"has_time": True, "has_date": False},
                "test_date": {"has_time": False, "has_date": True},
                "test_datetime": {"has_time": True, "has_date": True},
                "test_bogus_data": {
                    "has_time": True,
                    "has_date": True,
                    "initial": initial.strftime(FORMAT_DATETIME),
                },
                "test_was_time": {"has_time": False, "has_date": True},
                "test_was_date": {"has_time": True, "has_date": False},
            }
        },
    )

    dt_obj = datetime.datetime(2017, 9, 7, 19, 46)
    state_time = hass.states.get("input_datetime.test_time")
    expect(state_time.state).to_equal(dt_obj.strftime(FORMAT_TIME))

    state_date = hass.states.get("input_datetime.test_date")
    expect(state_date.state).to_equal(dt_obj.strftime(FORMAT_DATE))

    state_datetime = hass.states.get("input_datetime.test_datetime")
    expect(state_datetime.state).to_equal(dt_obj.strftime(FORMAT_DATETIME))

    state_bogus = hass.states.get("input_datetime.test_bogus_data")
    expect(state_bogus.state).to_equal(initial.strftime(FORMAT_DATETIME))

    state_was_time = hass.states.get("input_datetime.test_was_time")
    expect(state_was_time.state).to_equal(default.strftime(FORMAT_DATE))

    state_was_date = hass.states.get("input_datetime.test_was_date")
    expect(state_was_date.state).to_equal(default.strftime(FORMAT_TIME))


@test
async def default_value(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test default value if none has been set via initial or restore state."""
    await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "test_time": {"has_time": True, "has_date": False},
                "test_date": {"has_time": False, "has_date": True},
                "test_datetime": {"has_time": True, "has_date": True},
            }
        },
    )

    dt_obj = datetime.datetime.combine(datetime.date.today(), DEFAULT_TIME)
    state_time = hass.states.get("input_datetime.test_time")
    expect(state_time.state).to_equal(dt_obj.strftime(FORMAT_TIME))
    expect(state_time.attributes.get("timestamp")).not_.to_be_none()

    state_date = hass.states.get("input_datetime.test_date")
    expect(state_date.state).to_equal(dt_obj.strftime(FORMAT_DATE))
    expect(state_date.attributes.get("timestamp")).not_.to_be_none()

    state_datetime = hass.states.get("input_datetime.test_datetime")
    expect(state_datetime.state).to_equal(dt_obj.strftime(FORMAT_DATETIME))
    expect(state_datetime.attributes.get("timestamp")).not_.to_be_none()


@test
async def input_datetime_context(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test that input_datetime context works."""
    expect(
        await async_setup_component(
            hass,
            "input_datetime",
            {"input_datetime": {"only_date": {"has_date": True}}},
        )
    ).to_be(True)

    state = hass.states.get("input_datetime.only_date")
    expect(state).not_.to_be_none()

    await hass.services.async_call(
        "input_datetime",
        "set_datetime",
        {"entity_id": state.entity_id, "date": "2018-01-02"},
        blocking=True,
        context=Context(user_id=hass_admin_user.id),
    )

    state2 = hass.states.get("input_datetime.only_date")
    expect(state2).not_.to_be_none()
    expect(state.state != state2.state).to_be(True)
    expect(state2.context.user_id).to_equal(hass_admin_user.id)


@test
async def reload(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
    hass_read_only_user: MockUser = Depends(hass_read_only_user_fx),
) -> None:
    """Test reload service."""
    count_start = len(hass.states.async_entity_ids())

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "dt1": {
                        "has_time": False,
                        "has_date": True,
                        "initial": "2019-1-1",
                    },
                    "dt3": {CONF_HAS_TIME: True, CONF_HAS_DATE: True},
                }
            },
        )
    ).to_be(True)

    expect(count_start + 2).to_equal(len(hass.states.async_entity_ids()))

    state_1 = hass.states.get("input_datetime.dt1")
    state_2 = hass.states.get("input_datetime.dt2")
    state_3 = hass.states.get("input_datetime.dt3")

    dt_obj = datetime.datetime(2019, 1, 1, 0, 0)
    expect(state_1).not_.to_be_none()
    expect(state_2).to_be_none()
    expect(state_3).not_.to_be_none()
    expect(dt_obj.strftime(FORMAT_DATE)).to_equal(state_1.state)
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "dt1")
    ).to_equal(f"{DOMAIN}.dt1")
    expect(entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "dt2")).to_be_none()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "dt3")
    ).to_equal(f"{DOMAIN}.dt3")

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: {
                "dt1": {"has_time": True, "has_date": False, "initial": "23:32"},
                "dt2": {"has_time": True, "has_date": True},
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

    expect(count_start + 2).to_equal(len(hass.states.async_entity_ids()))

    state_1 = hass.states.get("input_datetime.dt1")
    state_2 = hass.states.get("input_datetime.dt2")
    state_3 = hass.states.get("input_datetime.dt3")

    expect(state_1).not_.to_be_none()
    expect(state_2).not_.to_be_none()
    expect(state_3).to_be_none()
    expect(state_1.state).to_equal(DEFAULT_TIME.strftime(FORMAT_TIME))
    expect(state_2.state).to_equal(
        datetime.datetime.combine(datetime.date.today(), DEFAULT_TIME).strftime(
            FORMAT_DATETIME
        )
    )

    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "dt1")
    ).to_equal(f"{DOMAIN}.dt1")
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "dt2")
    ).to_equal(f"{DOMAIN}.dt2")
    expect(entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "dt3")).to_be_none()


@test
async def load_from_storage(
    hass: HomeAssistant = Depends(hass_fixture),
    storage_setup: Callable[..., Awaitable[bool]] = Depends(storage_setup_fx),
) -> None:
    """Test set up from storage."""
    expect(await storage_setup()).to_be(True)
    state = hass.states.get(f"{DOMAIN}.datetime_from_storage")
    expect(state.state).to_equal(INITIAL_DATETIME)
    expect(state.attributes.get(ATTR_EDITABLE)).to_be(True)


@test
async def editable_state_attribute(
    hass: HomeAssistant = Depends(hass_fixture),
    storage_setup: Callable[..., Awaitable[bool]] = Depends(storage_setup_fx),
) -> None:
    """Test editable attribute."""
    expect(
        await storage_setup(
            config={
                DOMAIN: {
                    "from_yaml": {
                        CONF_HAS_DATE: True,
                        CONF_HAS_TIME: True,
                        CONF_NAME: "yaml datetime",
                        CONF_INITIAL: "2001-01-02 12:34:56",
                    }
                }
            }
        )
    ).to_be(True)

    state = hass.states.get(f"{DOMAIN}.datetime_from_storage")
    expect(state.state).to_equal(INITIAL_DATETIME)
    expect(state.attributes.get(ATTR_EDITABLE)).to_be(True)

    state = hass.states.get(f"{DOMAIN}.from_yaml")
    expect(state.state).to_equal("2001-01-02 12:34:56")
    expect(state.attributes[ATTR_EDITABLE]).to_be(False)


@test
async def ws_list(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Awaitable[bool]] = Depends(storage_setup_fx),
) -> None:
    """Test listing via WS."""
    expect(
        await storage_setup(config={DOMAIN: {"from_yaml": {CONF_HAS_DATE: True}}})
    ).to_be(True)

    client = await hass_ws_client(hass)

    await client.send_json({"id": 6, "type": f"{DOMAIN}/list"})
    resp = await client.receive_json()
    expect(resp["success"]).to_be(True)

    storage_ent = "from_storage"
    yaml_ent = "from_yaml"
    result = {item["id"]: item for item in resp["result"]}

    expect(len(result)).to_equal(1)
    expect(storage_ent in result).to_be(True)
    expect(yaml_ent in result).to_be(False)
    expect(result[storage_ent][ATTR_NAME]).to_equal("datetime from storage")


@test
async def ws_delete(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Awaitable[bool]] = Depends(storage_setup_fx),
) -> None:
    """Test WS delete cleans up entity registry."""
    expect(await storage_setup()).to_be(True)

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.datetime_from_storage"

    state = hass.states.get(input_entity_id)
    expect(state).not_.to_be_none()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id)
    ).to_equal(input_entity_id)

    client = await hass_ws_client(hass)

    await client.send_json(
        {"id": 6, "type": f"{DOMAIN}/delete", f"{DOMAIN}_id": f"{input_id}"}
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be(True)

    state = hass.states.get(input_entity_id)
    expect(state).to_be_none()
    expect(entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id)).to_be_none()


@test
async def update(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Awaitable[bool]] = Depends(storage_setup_fx),
) -> None:
    """Test updating min/max updates the state."""

    expect(await storage_setup()).to_be(True)

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.datetime_from_storage"

    state = hass.states.get(input_entity_id)
    expect(state.attributes[ATTR_FRIENDLY_NAME]).to_equal("datetime from storage")
    expect(state.state).to_equal(INITIAL_DATETIME)
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id)
    ).to_equal(input_entity_id)

    client = await hass_ws_client(hass)

    updated_settings = {
        CONF_NAME: "even newer name",
        CONF_HAS_DATE: False,
        CONF_HAS_TIME: True,
        CONF_INITIAL: INITIAL_DATETIME,
    }
    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": f"{input_id}",
            **updated_settings,
        }
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be(True)
    expect(resp["result"]).to_equal({"id": "from_storage"} | updated_settings)

    state = hass.states.get(input_entity_id)
    expect(state.state).to_equal(INITIAL_TIME)
    expect(state.attributes[ATTR_FRIENDLY_NAME]).to_equal("even newer name")


@test
async def ws_create(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Awaitable[bool]] = Depends(storage_setup_fx),
) -> None:
    """Test create WS."""
    expect(await storage_setup(items=[])).to_be(True)

    input_id = "new_datetime"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    expect(state).to_be_none()
    expect(entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id)).to_be_none()

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/create",
            CONF_NAME: "New DateTime",
            CONF_INITIAL: "1991-01-02 01:02:03",
            CONF_HAS_DATE: True,
            CONF_HAS_TIME: True,
        }
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be(True)

    state = hass.states.get(input_entity_id)
    expect(state.state).to_equal("1991-01-02 01:02:03")
    expect(state.attributes[ATTR_FRIENDLY_NAME]).to_equal("New DateTime")
    expect(state.attributes[ATTR_EDITABLE]).to_be(True)


@test
async def setup_no_config(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test component setup with no config."""
    count_start = len(hass.states.async_entity_ids())
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)

    with patch(
        "homeassistant.config.load_yaml_config_file", autospec=True, return_value={}
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id=hass_admin_user.id),
        )

    expect(count_start).to_equal(len(hass.states.async_entity_ids()))


@test
async def timestamp(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test timestamp."""
    await hass.config.async_set_time_zone("America/Los_Angeles")

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "test_datetime_initial_with_tz": {
                        "has_time": True,
                        "has_date": True,
                        "initial": "2020-12-13 10:00:00+01:00",
                    },
                    "test_datetime_initial_without_tz": {
                        "has_time": True,
                        "has_date": True,
                        "initial": "2020-12-13 10:00:00",
                    },
                    "test_time_initial": {
                        "has_time": True,
                        "has_date": False,
                        "initial": "10:00:00",
                    },
                }
            },
        )
    ).to_be(True)

    # initial has been converted to the set timezone
    state_with_tz = hass.states.get("input_datetime.test_datetime_initial_with_tz")
    expect(state_with_tz).not_.to_be_none()
    # Timezone LA is UTC-8 => timestamp carries +01:00 => delta is -9 => 10:00 - 09:00 => 01:00
    expect(state_with_tz.state).to_equal("2020-12-13 01:00:00")
    expect(
        dt_util.as_local(
            dt_util.utc_from_timestamp(state_with_tz.attributes[ATTR_TIMESTAMP])
        ).strftime(FORMAT_DATETIME)
    ).to_equal("2020-12-13 01:00:00")

    # initial has been interpreted as being part of set timezone
    state_without_tz = hass.states.get(
        "input_datetime.test_datetime_initial_without_tz"
    )
    expect(state_without_tz).not_.to_be_none()
    expect(state_without_tz.state).to_equal("2020-12-13 10:00:00")
    # Timezone LA is UTC-8 => timestamp has no zone (= assumed local) => delta to UTC is +8 => 10:00 + 08:00 => 18:00
    expect(
        dt_util.utc_from_timestamp(
            state_without_tz.attributes[ATTR_TIMESTAMP]
        ).strftime(FORMAT_DATETIME)
    ).to_equal("2020-12-13 18:00:00")
    expect(
        dt_util.as_local(
            dt_util.utc_from_timestamp(state_without_tz.attributes[ATTR_TIMESTAMP])
        ).strftime(FORMAT_DATETIME)
    ).to_equal("2020-12-13 10:00:00")
    # Use datetime.datetime.fromtimestamp
    expect(
        dt_util.as_local(
            datetime.datetime.fromtimestamp(
                state_without_tz.attributes[ATTR_TIMESTAMP], datetime.UTC
            )
        ).strftime(FORMAT_DATETIME)
    ).to_equal("2020-12-13 10:00:00")

    # Test initial time sets timestamp correctly.
    state_time = hass.states.get("input_datetime.test_time_initial")
    expect(state_time).not_.to_be_none()
    expect(state_time.state).to_equal("10:00:00")
    expect(state_time.attributes[ATTR_TIMESTAMP]).to_equal(10 * 60 * 60)

    # Test that setting the timestamp of an entity works.
    await hass.services.async_call(
        DOMAIN,
        "set_datetime",
        {
            ATTR_ENTITY_ID: "input_datetime.test_datetime_initial_with_tz",
            ATTR_TIMESTAMP: state_without_tz.attributes[ATTR_TIMESTAMP],
        },
        blocking=True,
    )
    state_with_tz_updated = hass.states.get(
        "input_datetime.test_datetime_initial_with_tz"
    )
    expect(state_with_tz_updated.state).to_equal("2020-12-13 10:00:00")
    expect(state_with_tz_updated.attributes[ATTR_TIMESTAMP]).to_equal(
        state_without_tz.attributes[ATTR_TIMESTAMP]
    )


@test.cases(
    test.case(
        "datetime",
        config={"has_time": True, "has_date": True, "initial": "abc"},
        error="'abc' can't be parsed as a datetime",
    ),
    test.case(
        "date",
        config={"has_time": False, "has_date": True, "initial": "abc"},
        error="'abc' can't be parsed as a date",
    ),
    test.case(
        "time",
        config={"has_time": True, "has_date": False, "initial": "abc"},
        error="'abc' can't be parsed as a time",
    ),
)
async def invalid_initial(
    config: dict[str, Any],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test configuration is rejected if the initial value is invalid."""
    expect(
        await async_setup_component(hass, DOMAIN, {DOMAIN: {"test_date": config}})
    ).to_be(False)
    expect(caplog.text).to_contain(error)
