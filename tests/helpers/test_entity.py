"""Test the entity helper."""

import asyncio
import dataclasses
import threading
from unittest.mock import MagicMock, PropertyMock, patch

import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_DEVICE_CLASS,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    EntityCategory,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity, entity_registry as er

from tests.common import (
    MockConfigEntry,
    MockEntity,
    MockEntityPlatform,
    RegistryEntryWithDefaults,
    mock_registry,
)
from tests.hass_fixtures import caplog, entity_registry, hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
def generate_entity_id_requires_hass_or_ids() -> None:
    """Ensure we require at least hass or current ids."""
    expect(lambda: entity.generate_entity_id("test.{}", "hello world")).to_raise(
        ValueError
    )


@test
def generate_entity_id_given_keys() -> None:
    """Test generating an entity id given current ids."""
    expect(
        entity.generate_entity_id(
            "test.{}",
            "overwrite hidden true",
            current_ids=["test.overwrite_hidden_true"],
        )
    ).to_equal("test.overwrite_hidden_true_2")
    expect(
        entity.generate_entity_id(
            "test.{}", "overwrite hidden true", current_ids=["test.another_entity"]
        )
    ).to_equal("test.overwrite_hidden_true")


@test
async def generate_entity_id_given_hass(hass: HomeAssistant = Depends(hass)) -> None:
    """Test generating an entity id given hass object."""
    hass.states.async_set("test.overwrite_hidden_true", "test")

    fmt = "test.{}"
    expect(
        entity.generate_entity_id(fmt, "overwrite hidden true", hass=hass)
    ).to_equal("test.overwrite_hidden_true_2")


@test
async def async_update_support(hass: HomeAssistant = Depends(hass)) -> None:
    """Test async update getting called."""
    sync_update = []
    async_update = []

    class AsyncEntity(entity.Entity):
        """A test entity."""

        entity_id = "sensor.test"

        def update(self):
            """Update entity."""
            sync_update.append([1])

    ent = AsyncEntity()
    ent.hass = hass

    await ent.async_update_ha_state(True)

    expect(len(sync_update)).to_equal(1)
    expect(len(async_update)).to_equal(0)

    async def async_update_func():
        """Async update."""
        async_update.append(1)

    ent.async_update = async_update_func

    await ent.async_update_ha_state(True)

    expect(len(sync_update)).to_equal(1)
    expect(len(async_update)).to_equal(1)


@test
async def device_class(hass: HomeAssistant = Depends(hass)) -> None:
    """Test device class attribute."""
    ent = entity.Entity()
    ent.entity_id = "test.overwrite_hidden_true"
    ent.hass = hass
    ent.async_write_ha_state()
    state = hass.states.get(ent.entity_id)
    expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_be_none()

    ent._attr_device_class = "test_class"
    ent.async_write_ha_state()
    state = hass.states.get(ent.entity_id)
    expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_equal("test_class")


@test
async def warn_slow_update(
    hass: HomeAssistant = Depends(hass),
    caplog=Depends(caplog),
) -> None:
    """Warn we log when entity update takes a long time."""
    update_call = False

    async def async_update():
        """Mock async update."""
        nonlocal update_call
        await asyncio.sleep(0.00001)
        update_call = True

    mock_entity = entity.Entity()
    mock_entity.hass = hass
    mock_entity.entity_id = "comp_test.test_entity"
    mock_entity.async_update = async_update

    fast_update_time = 0.0000001

    with patch.object(entity, "SLOW_UPDATE_WARNING", fast_update_time):
        await mock_entity.async_update_ha_state(True)
        expect(str(fast_update_time) in caplog.text).to_be(True)
        expect(mock_entity.entity_id in caplog.text).to_be(True)
        expect(update_call).to_be(True)


@test
async def warn_slow_update_with_exception(
    hass: HomeAssistant = Depends(hass),
    caplog=Depends(caplog),
) -> None:
    """Warn we log when entity update takes a long time and throws exception."""
    update_call = False

    async def async_update():
        """Mock async update."""
        nonlocal update_call
        update_call = True
        await asyncio.sleep(0.00001)
        raise AssertionError("Fake update error")

    mock_entity = entity.Entity()
    mock_entity.hass = hass
    mock_entity.entity_id = "comp_test.test_entity"
    mock_entity.async_update = async_update

    fast_update_time = 0.0000001

    with patch.object(entity, "SLOW_UPDATE_WARNING", fast_update_time):
        await mock_entity.async_update_ha_state(True)
        expect(str(fast_update_time) in caplog.text).to_be(True)
        expect(mock_entity.entity_id in caplog.text).to_be(True)
        expect(update_call).to_be(True)


@test
async def warn_slow_device_update_disabled(
    hass: HomeAssistant = Depends(hass),
    caplog=Depends(caplog),
) -> None:
    """Disable slow update warning with async_device_update."""
    update_call = False

    async def async_update():
        """Mock async update."""
        nonlocal update_call
        await asyncio.sleep(0.00001)
        update_call = True

    mock_entity = entity.Entity()
    mock_entity.hass = hass
    mock_entity.entity_id = "comp_test.test_entity"
    mock_entity.async_update = async_update

    fast_update_time = 0.0000001

    with patch.object(entity, "SLOW_UPDATE_WARNING", fast_update_time):
        await mock_entity.async_device_update(warning=False)
        expect(str(fast_update_time) not in caplog.text).to_be(True)
        expect(mock_entity.entity_id not in caplog.text).to_be(True)
        expect(update_call).to_be(True)


@test
async def async_schedule_update_ha_state(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test async_schedule_update_ha_state."""
    update_call = False

    async def async_update():
        """Mock async update."""
        nonlocal update_call
        update_call = True

    mock_entity = entity.Entity()
    mock_entity.hass = hass
    mock_entity.entity_id = "comp_test.test_entity"
    mock_entity.async_update = async_update

    mock_entity.async_schedule_update_ha_state(True)
    await hass.async_block_till_done()

    expect(update_call).to_be(True)


@test
async def async_async_request_call_without_lock(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test for async_requests_call works without a lock."""
    updates = []

    class AsyncEntity(entity.Entity):
        """Test entity."""

        def __init__(self, entity_id: str) -> None:
            """Initialize Async test entity."""
            self.entity_id = entity_id
            self.hass = hass

        async def testhelper(self, count: int) -> None:
            """Helper function."""
            updates.append(count)

    ent_1 = AsyncEntity("light.test_1")
    ent_2 = AsyncEntity("light.test_2")
    job1 = ent_1.async_request_call(ent_1.testhelper(1))
    job2 = ent_2.async_request_call(ent_2.testhelper(2))

    await asyncio.gather(job1, job2)
    while True:
        if len(updates) >= 2:
            break
        await asyncio.sleep(0)

    expect(len(updates)).to_equal(2)
    updates.sort()
    expect(updates).to_equal([1, 2])


@test
async def async_async_request_call_with_lock(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test for async_requests_call works with a semaphore."""
    updates = []

    test_semaphore = asyncio.Semaphore(1)

    class AsyncEntity(entity.Entity):
        """Test entity."""

        def __init__(self, entity_id: str, lock: asyncio.Semaphore) -> None:
            """Initialize Async test entity."""
            self.entity_id = entity_id
            self.hass = hass
            self.parallel_updates = lock

        async def testhelper(self, count):
            """Helper function."""
            updates.append(count)

    ent_1 = AsyncEntity("light.test_1", test_semaphore)
    ent_2 = AsyncEntity("light.test_2", test_semaphore)

    try:
        expect(test_semaphore.locked()).to_be(False)
        await test_semaphore.acquire()
        expect(test_semaphore.locked()).to_be_truthy()

        job1 = ent_1.async_request_call(ent_1.testhelper(1))
        job2 = ent_2.async_request_call(ent_2.testhelper(2))

        hass.async_create_task(job1)
        hass.async_create_task(job2)

        expect(len(updates)).to_equal(0)
        expect(updates).to_equal([])
        expect(test_semaphore._value).to_equal(0)

        test_semaphore.release()

        while True:
            if len(updates) >= 2:
                break
            await asyncio.sleep(0)
    finally:
        test_semaphore.release()

    expect(len(updates)).to_equal(2)
    updates.sort()
    expect(updates).to_equal([1, 2])


@test
async def async_parallel_updates_with_zero(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test parallel updates with 0 (disabled)."""
    updates = []
    test_lock = asyncio.Event()

    class AsyncEntity(entity.Entity):
        """Test entity."""

        def __init__(self, entity_id: str, count: int) -> None:
            """Initialize Async test entity."""
            self.entity_id = entity_id
            self.hass = hass
            self._count = count

        async def async_update(self) -> None:
            """Test update."""
            updates.append(self._count)
            await test_lock.wait()

    ent_1 = AsyncEntity("sensor.test_1", 1)
    ent_2 = AsyncEntity("sensor.test_2", 2)

    try:
        ent_1.async_schedule_update_ha_state(True)
        ent_2.async_schedule_update_ha_state(True)

        while True:
            if len(updates) >= 2:
                break
            await asyncio.sleep(0)

        expect(len(updates)).to_equal(2)
        expect(updates).to_equal([1, 2])
    finally:
        test_lock.set()


@test
async def async_parallel_updates_with_zero_on_sync_update(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test parallel updates with 0 (disabled)."""
    updates = []
    test_lock = threading.Event()

    class AsyncEntity(entity.Entity):
        """Test entity."""

        def __init__(self, entity_id: str, count: int) -> None:
            """Initialize Async test entity."""
            self.entity_id = entity_id
            self.hass = hass
            self._count = count

        def update(self):
            """Test update."""
            updates.append(self._count)
            if not test_lock.wait(timeout=1):
                updates.append(self._count)

    ent_1 = AsyncEntity("sensor.test_1", 1)
    ent_2 = AsyncEntity("sensor.test_2", 2)

    try:
        ent_1.async_schedule_update_ha_state(True)
        ent_2.async_schedule_update_ha_state(True)

        while True:
            if len(updates) >= 2:
                break
            await asyncio.sleep(0)

        expect(len(updates)).to_equal(2)
        expect(sorted(updates)).to_equal([1, 2])
    finally:
        test_lock.set()
        await asyncio.sleep(0)


@test
async def async_remove_no_platform(hass: HomeAssistant = Depends(hass)) -> None:
    """Test async_remove method when no platform set."""
    ent = entity.Entity()
    ent.hass = hass
    ent.entity_id = "test.test"
    expect(ent._platform_state).to_be(entity.EntityPlatformState.NOT_ADDED)
    ent.async_write_ha_state()
    expect(ent._platform_state).to_be(entity.EntityPlatformState.NOT_ADDED)
    expect(len(hass.states.async_entity_ids())).to_equal(1)
    await ent.async_remove()
    expect(len(hass.states.async_entity_ids())).to_equal(0)
    expect(ent._platform_state).to_be(entity.EntityPlatformState.REMOVED)


@test
async def async_remove_runs_callbacks(hass: HomeAssistant = Depends(hass)) -> None:
    """Test async_remove runs on_remove callback."""
    result = []

    platform = MockEntityPlatform(hass, domain="test")
    ent = entity.Entity()
    ent.entity_id = "test.test"
    expect(ent._platform_state).to_be(entity.EntityPlatformState.NOT_ADDED)
    await platform.async_add_entities([ent])
    expect(ent._platform_state).to_be(entity.EntityPlatformState.ADDED)
    ent.async_on_remove(lambda: result.append(1))
    await ent.async_remove()
    expect(len(result)).to_equal(1)
    expect(ent._platform_state).to_be(entity.EntityPlatformState.REMOVED)


@test
async def async_remove_ignores_in_flight_polling(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test in flight polling is ignored after removing."""
    result = []

    platform = MockEntityPlatform(hass, domain="test")
    ent = entity.Entity()
    ent.entity_id = "test.test"
    ent.async_on_remove(lambda: result.append(1))
    await platform.async_add_entities([ent])
    expect(hass.states.get("test.test").state).to_equal(STATE_UNKNOWN)

    await ent.async_remove()
    expect(len(result)).to_equal(1)
    expect(hass.states.get("test.test")).to_be_none()

    ent.async_write_ha_state()
    expect(len(result)).to_equal(1)
    expect(hass.states.get("test.test")).to_be_none()


@test
async def async_remove_twice(hass: HomeAssistant = Depends(hass)) -> None:
    """Test removing an entity twice only cleans up once."""
    result = []

    class MockEnt(entity.Entity):
        def __init__(self) -> None:
            self.remove_calls = []

        async def async_will_remove_from_hass(self) -> None:
            self.remove_calls.append(None)

    platform = MockEntityPlatform(hass, domain="test")
    ent = MockEnt()
    ent.hass = hass
    ent.entity_id = "test.test"
    ent.async_on_remove(lambda: result.append(1))
    await platform.async_add_entities([ent])
    expect(hass.states.get("test.test").state).to_equal(STATE_UNKNOWN)

    await ent.async_remove()
    expect(len(result)).to_equal(1)
    expect(len(ent.remove_calls)).to_equal(1)
    expect(ent._platform_state).to_be(entity.EntityPlatformState.REMOVED)

    await ent.async_remove()
    expect(len(result)).to_equal(1)
    expect(len(ent.remove_calls)).to_equal(1)
    expect(ent._platform_state).to_be(entity.EntityPlatformState.REMOVED)


@test
async def set_context(hass: HomeAssistant = Depends(hass)) -> None:
    """Test setting context."""
    context = Context()
    ent = entity.Entity()
    ent.hass = hass
    ent.entity_id = "hello.world"
    ent.async_set_context(context)
    ent.async_write_ha_state()
    expect(hass.states.get("hello.world").context).to_be(context)


@test
async def set_context_expired(hass: HomeAssistant = Depends(hass)) -> None:
    """Test setting context."""
    context = Context()

    with patch("homeassistant.helpers.entity.CONTEXT_RECENT_TIME_SECONDS", -5):
        ent = entity.Entity()
        ent.hass = hass
        ent.entity_id = "hello.world"
        ent.async_set_context(context)
        ent.async_write_ha_state()

    expect(hass.states.get("hello.world").context != context).to_be(True)
    expect(ent._context).to_be_none()
    expect(ent._context_set).to_be_none()


@test
async def warn_disabled(
    hass: HomeAssistant = Depends(hass),
    caplog=Depends(caplog),
) -> None:
    """Test we warn once if we write to a disabled entity."""
    entry = RegistryEntryWithDefaults(
        entity_id="hello.world",
        unique_id="test-unique-id",
        platform="test-platform",
        disabled_by=er.RegistryEntryDisabler.USER,
    )
    mock_registry(hass, {"hello.world": entry})

    ent = entity.Entity()
    ent.hass = hass
    ent.entity_id = "hello.world"
    ent.registry_entry = entry
    ent.platform = MagicMock(platform_name="test-platform")

    caplog.clear()
    ent.async_write_ha_state()
    expect(hass.states.get("hello.world")).to_be_none()
    expect(
        "Entity hello.world is incorrectly being triggered" in caplog.text
    ).to_be(True)

    caplog.clear()
    ent.async_write_ha_state()
    expect(hass.states.get("hello.world")).to_be_none()
    expect(caplog.text).to_equal("")


@test
async def disabled_in_entity_registry(hass: HomeAssistant = Depends(hass)) -> None:
    """Test entity is removed if we disable entity registry entry."""
    entry = RegistryEntryWithDefaults(
        entity_id="hello.world",
        unique_id="test-unique-id",
        platform="test-platform",
        disabled_by=None,
    )
    registry = mock_registry(hass, {"hello.world": entry})

    ent = entity.Entity()
    ent.hass = hass
    ent.entity_id = "hello.world"
    ent.registry_entry = entry
    expect(ent.enabled).to_be(True)

    ent.add_to_platform_start(hass, MagicMock(platform_name="test-platform"), None)
    await ent.add_to_platform_finish()
    expect(hass.states.get("hello.world")).not_.to_be_none()

    entry2 = registry.async_update_entity(
        "hello.world", disabled_by=er.RegistryEntryDisabler.USER
    )
    await hass.async_block_till_done()
    expect(entry2 != entry).to_be(True)
    expect(ent.registry_entry).to_equal(entry2)
    expect(ent.enabled).to_be(False)
    expect(hass.states.get("hello.world")).to_be_none()

    entry3 = registry.async_update_entity("hello.world", disabled_by=None)
    await hass.async_block_till_done()
    expect(entry3 != entry2).to_be(True)
    expect(ent.registry_entry).to_equal(entry2)


@test
async def capability_attrs(hass: HomeAssistant = Depends(hass)) -> None:
    """Test we still include capabilities even when unavailable."""
    with (
        patch.object(entity.Entity, "available", PropertyMock(return_value=False)),
        patch.object(
            entity.Entity,
            "capability_attributes",
            PropertyMock(return_value={"always": "there"}),
        ),
    ):
        ent = entity.Entity()
        ent.hass = hass
        ent.entity_id = "hello.world"
        ent.async_write_ha_state()

    state = hass.states.get("hello.world")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_UNAVAILABLE)
    expect(state.attributes["always"]).to_equal("there")


@test
async def warn_slow_write_state(
    hass: HomeAssistant = Depends(hass),
    caplog=Depends(caplog),
) -> None:
    """Check that we log a warning if reading properties takes too long."""
    mock_entity = entity.Entity()
    mock_entity.hass = hass
    mock_entity.entity_id = "comp_test.test_entity"
    mock_entity.platform_data = MagicMock(platform_name="hue")
    mock_entity._platform_state = entity.EntityPlatformState.ADDED

    with patch("homeassistant.helpers.entity.timer", side_effect=[0, 10]):
        mock_entity.async_write_ha_state()

    expect(
        (
            "Updating state for comp_test.test_entity "
            "(<class 'homeassistant.helpers.entity.Entity'>) "
            "took 10.000 seconds. Please create a bug report at "
            "https://github.com/home-assistant/core/issues?"
            "q=is%3Aopen+is%3Aissue+label%3A%22integration%3A+hue%22"
        )
        in caplog.text
    ).to_be(True)


@test
async def setup_source(hass: HomeAssistant = Depends(hass)) -> None:
    """Check that we register sources correctly."""
    platform = MockEntityPlatform(hass)

    entity_platform = MockEntity(name="Platform Config Source")
    await platform.async_add_entities([entity_platform])

    platform.config_entry = MockConfigEntry()
    entity_entry = MockEntity(name="Config Entry Source")
    await platform.async_add_entities([entity_entry])

    expect(entity.entity_sources(hass)).to_equal(
        {
            "test_domain.platform_config_source": {
                "domain": "test_platform",
            },
            "test_domain.config_entry_source": {
                "config_entry": platform.config_entry.entry_id,
                "domain": "test_platform",
            },
        }
    )

    await platform.async_reset()

    expect(entity.entity_sources(hass)).to_equal({})


@test
async def removing_entity_unavailable(hass: HomeAssistant = Depends(hass)) -> None:
    """Test removing a still-registered entity creates an unavailable state."""
    platform = MockEntityPlatform(hass, domain="hello")
    ent = entity.Entity()
    ent.entity_id = "hello.world"
    ent._attr_unique_id = "test-unique-id"
    await platform.async_add_entities([ent])

    state = hass.states.get("hello.world")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_UNKNOWN)

    await ent.async_remove()

    state = hass.states.get("hello.world")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_UNAVAILABLE)


@test
async def get_supported_features_entity_registry(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test get_supported_features falls back to entity registry."""
    entity_id = entity_registry.async_get_or_create(
        "hello", "world", "5678", supported_features=456
    ).entity_id
    expect(entity.get_supported_features(hass, entity_id)).to_equal(456)


@test
async def get_supported_features_prioritize_state(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test get_supported_features gives priority to state."""
    entity_id = entity_registry.async_get_or_create(
        "hello", "world", "5678", supported_features=456
    ).entity_id
    expect(entity.get_supported_features(hass, entity_id)).to_equal(456)

    hass.states.async_set(entity_id, None, {"supported_features": 123})

    expect(entity.get_supported_features(hass, entity_id)).to_equal(123)


@test
async def get_supported_features_raises_on_unknown(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test get_supported_features raises on unknown entity_id."""
    expect(
        lambda: entity.get_supported_features(hass, "hello.world")
    ).to_raise(HomeAssistantError)


@test
async def float_conversion(hass: HomeAssistant = Depends(hass)) -> None:
    """Test conversion of float state to string rounds."""
    expect(2.4 + 1.2 != 3.6).to_be(True)
    with patch.object(entity.Entity, "state", PropertyMock(return_value=2.4 + 1.2)):
        ent = entity.Entity()
        ent.hass = hass
        ent.entity_id = "hello.world"
        ent.async_write_ha_state()

    state = hass.states.get("hello.world")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("3.6")


@test
async def attribution_attribute(hass: HomeAssistant = Depends(hass)) -> None:
    """Test attribution attribute."""
    mock_entity = entity.Entity()
    mock_entity.hass = hass
    mock_entity.entity_id = "hello.world"
    mock_entity._attr_attribution = "Home Assistant"

    mock_entity.async_schedule_update_ha_state(True)
    await hass.async_block_till_done()

    state = hass.states.get(mock_entity.entity_id)
    expect(state.attributes.get(ATTR_ATTRIBUTION)).to_equal("Home Assistant")


@test
async def entity_category_property(hass: HomeAssistant = Depends(hass)) -> None:
    """Test entity category property."""
    mock_entity1 = entity.Entity()
    mock_entity1.hass = hass
    mock_entity1.entity_description = entity.EntityDescription(
        key="abc", entity_category="ignore_me"
    )
    mock_entity1.entity_id = "hello.world"
    mock_entity1._attr_entity_category = EntityCategory.CONFIG
    expect(mock_entity1.entity_category).to_equal("config")

    mock_entity2 = entity.Entity()
    mock_entity2.hass = hass
    mock_entity2.entity_description = entity.EntityDescription(
        key="abc", entity_category=EntityCategory.CONFIG
    )
    mock_entity2.entity_id = "hello.world"
    expect(mock_entity2.entity_category).to_equal("config")


@test.cases(
    test.case("config", value="config", expected=EntityCategory.CONFIG),
    test.case("diagnostic", value="diagnostic", expected=EntityCategory.DIAGNOSTIC),
)
def entity_category_schema(value: str, expected: EntityCategory) -> None:
    """Test entity category schema."""
    schema = vol.Schema(entity.ENTITY_CATEGORIES_SCHEMA)
    result = schema(value)
    expect(result).to_equal(expected)
    expect(isinstance(result, EntityCategory)).to_be(True)


@test.cases(
    test.case("none", value=None),
    test.case("non_existing", value="non_existing"),
)
def entity_category_schema_error(value: str | None) -> None:
    """Test entity category schema error."""
    schema = vol.Schema(entity.ENTITY_CATEGORIES_SCHEMA)
    expect(lambda: schema(value)).to_raise(
        vol.Invalid,
        match=r"expected EntityCategory or one of 'config', 'diagnostic'",
    )


@test
async def entity_description_fallback() -> None:
    """Test entity description has same defaults as entity."""
    ent = entity.Entity()
    ent_with_description = entity.Entity()
    ent_with_description.entity_description = entity.EntityDescription(key="test")

    for field in dataclasses.fields(entity.EntityDescription._dataclass):
        if field.name == "key":
            continue

        expect(getattr(ent, field.name)).to_equal(
            getattr(ent_with_description, field.name)
        )
