"""The tests for the Entity component helper."""

from collections import OrderedDict
from datetime import timedelta
import logging
import re
from unittest.mock import AsyncMock, Mock, patch

from freezegun import freeze_time
from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant.const import (
    ENTITY_MATCH_ALL,
    ENTITY_MATCH_NONE,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import (
    EntityServiceResponse,
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError, PlatformNotReady
from homeassistant.helpers import config_validation as cv, discovery
from homeassistant.helpers.entity_component import EntityComponent, async_update_entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.service import async_get_all_descriptions
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import (
    MockConfigEntry,
    MockEntity,
    MockModule,
    MockPlatform,
    async_fire_time_changed,
    mock_integration,
    mock_platform,
)
from tests.hass_fixtures import hass

_LOGGER = logging.getLogger(__name__)
DOMAIN = "test_domain"


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def setup_loads_platforms(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the loading of the platforms."""
    component_setup = Mock(return_value=True)
    platform_setup = Mock(return_value=None)

    mock_integration(hass, MockModule("test_component", setup=component_setup))
    mock_integration(hass, MockModule("mod2", dependencies=["test_component"]))
    mock_platform(hass, "mod2.test_domain", MockPlatform(setup_platform=platform_setup))

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    expect(component_setup.called).to_be(False)
    expect(platform_setup.called).to_be(False)

    component.setup({DOMAIN: {"platform": "mod2"}})

    await hass.async_block_till_done()
    expect(component_setup.called).to_be(True)
    expect(platform_setup.called).to_be(True)


@test
async def setup_recovers_when_setup_raises(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test the setup if exceptions are happening."""
    platform1_setup = Mock(side_effect=Exception("Broken"))
    platform2_setup = Mock(return_value=None)

    mock_platform(
        hass, "mod1.test_domain", MockPlatform(setup_platform=platform1_setup)
    )
    mock_platform(
        hass, "mod2.test_domain", MockPlatform(setup_platform=platform2_setup)
    )

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    expect(platform1_setup.called).to_be(False)
    expect(platform2_setup.called).to_be(False)

    component.setup(
        OrderedDict(
            [
                (DOMAIN, {"platform": "mod1"}),
                (f"{DOMAIN} 2", {"platform": "non_exist"}),
                (f"{DOMAIN} 3", {"platform": "mod2"}),
            ]
        )
    )

    await hass.async_block_till_done()
    expect(platform1_setup.called).to_be(True)
    expect(platform2_setup.called).to_be(True)


@test
async def setup_does_discovery(hass: HomeAssistant = Depends(hass)) -> None:
    """Test setup for discovery."""
    with (
        patch(
            "homeassistant.helpers.entity_component.EntityComponent.async_setup_platform",
        ) as mock_setup,
        patch("homeassistant.setup.async_setup_component", return_value=True),
    ):
        component = EntityComponent(_LOGGER, DOMAIN, hass)

        component.setup({})

        discovery.load_platform(
            hass, DOMAIN, "platform_test", {"msg": "discovery_info"}, {DOMAIN: {}}
        )

        await hass.async_block_till_done()

        expect(mock_setup.called).to_be(True)
        expect(mock_setup.call_args[0]).to_equal(
            ("platform_test", {}, {"msg": "discovery_info"})
        )


@test
async def set_scan_interval_via_config(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test the setting of the scan interval via configuration."""

    async def async_platform_setup(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> None:
        async_add_entities([MockEntity(should_poll=True)])

    mock_platform(
        hass,
        "platform.test_domain",
        MockPlatform(async_setup_platform=async_platform_setup),
    )

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    with patch.object(hass.loop, "call_later") as mock_track:
        await component.async_setup(
            {DOMAIN: {"platform": "platform", "scan_interval": timedelta(seconds=30)}}
        )

        await hass.async_block_till_done()
    expect(mock_track.called).to_be(True)
    expect(mock_track.call_args[0][0]).to_equal(30.0)


@test
async def set_entity_namespace_via_config(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test setting an entity namespace."""

    async def async_platform_setup(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> None:
        async_add_entities([MockEntity(name="beer"), MockEntity(name=None)])

    platform = MockPlatform(async_setup_platform=async_platform_setup)

    mock_platform(hass, "platform.test_domain", platform)

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    await component.async_setup(
        {DOMAIN: {"platform": "platform", "entity_namespace": "yummy"}}
    )

    await hass.async_block_till_done()

    expect(sorted(hass.states.async_entity_ids())).to_equal(
        [
            "test_domain.yummy_beer",
            "test_domain.yummy_unnamed_device",
        ]
    )


@test
async def extract_from_service_available_device(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test the extraction of entity from service and device is available."""
    component = EntityComponent(_LOGGER, DOMAIN, hass)
    await component.async_setup({})
    await component.async_add_entities(
        [
            MockEntity(name="test_1"),
            MockEntity(name="test_2", available=False),
            MockEntity(name="test_3"),
            MockEntity(name="test_4", available=False),
        ]
    )

    call_1 = ServiceCall(hass, "test", "service", data={"entity_id": ENTITY_MATCH_ALL})

    expect(
        sorted(
            ent.entity_id
            for ent in (await component.async_extract_from_service(call_1))
        )
    ).to_equal(["test_domain.test_1", "test_domain.test_3"])

    call_2 = ServiceCall(
        hass,
        "test",
        "service",
        data={"entity_id": ["test_domain.test_3", "test_domain.test_4"]},
    )

    expect(
        sorted(
            ent.entity_id
            for ent in (await component.async_extract_from_service(call_2))
        )
    ).to_equal(["test_domain.test_3"])


@test
async def platform_not_ready(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that we retry when platform not ready."""
    platform1_setup = Mock(side_effect=[PlatformNotReady, PlatformNotReady, None])
    mock_integration(hass, MockModule("mod1"))
    mock_platform(
        hass, "mod1.test_domain", MockPlatform(setup_platform=platform1_setup)
    )

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    utcnow = dt_util.utcnow()

    with freeze_time(utcnow):
        await component.async_setup({DOMAIN: {"platform": "mod1"}})
        await hass.async_block_till_done()
        expect(len(platform1_setup.mock_calls)).to_equal(1)
        expect("mod1.test_domain" in hass.config.components).to_be(False)

        async_fire_time_changed(hass, utcnow + timedelta(seconds=29))
        await hass.async_block_till_done()
        expect(len(platform1_setup.mock_calls)).to_equal(1)

        async_fire_time_changed(hass, utcnow + timedelta(seconds=30))
        await hass.async_block_till_done()
        expect(len(platform1_setup.mock_calls)).to_equal(2)
        expect("mod1.test_domain" in hass.config.components).to_be(False)

        async_fire_time_changed(hass, utcnow + timedelta(seconds=59))
        await hass.async_block_till_done()
        expect(len(platform1_setup.mock_calls)).to_equal(2)

        async_fire_time_changed(hass, utcnow + timedelta(seconds=60))
        await hass.async_block_till_done()
        expect(len(platform1_setup.mock_calls)).to_equal(3)
        expect("mod1.test_domain" in hass.config.components).to_be(True)


@test
async def extract_from_service_fails_if_no_entity_id(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test the extraction of everything from service."""
    component = EntityComponent(_LOGGER, DOMAIN, hass)
    await component.async_setup({})
    await component.async_add_entities(
        [MockEntity(name="test_1"), MockEntity(name="test_2")]
    )

    expect(
        await component.async_extract_from_service(ServiceCall(hass, "test", "service"))
    ).to_equal([])
    expect(
        await component.async_extract_from_service(
            ServiceCall(hass, "test", "service", {"entity_id": ENTITY_MATCH_NONE})
        )
    ).to_equal([])
    expect(
        await component.async_extract_from_service(
            ServiceCall(hass, "test", "service", {"area_id": ENTITY_MATCH_NONE})
        )
    ).to_equal([])


@test
async def extract_from_service_filter_out_non_existing_entities(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test the extraction of non existing entities from service."""
    component = EntityComponent(_LOGGER, DOMAIN, hass)
    await component.async_setup({})
    await component.async_add_entities(
        [MockEntity(name="test_1"), MockEntity(name="test_2")]
    )

    call = ServiceCall(
        hass,
        "test",
        "service",
        {"entity_id": ["test_domain.test_2", "test_domain.non_exist"]},
    )

    expect(
        [ent.entity_id for ent in await component.async_extract_from_service(call)]
    ).to_equal(["test_domain.test_2"])


@test
async def extract_from_service_no_group_expand(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test not expanding a group."""
    component = EntityComponent(_LOGGER, DOMAIN, hass)
    await component.async_setup({})
    await component.async_add_entities([MockEntity(entity_id="test_domain.test_group")])

    call = ServiceCall(
        hass, "test", "service", {"entity_id": ["test_domain.test_group"]}
    )

    extracted = await component.async_extract_from_service(call, expand_group=False)
    expect(len(extracted)).to_equal(1)
    expect(extracted[0].entity_id).to_equal("test_domain.test_group")


@test
async def setup_dependencies_platform(hass: HomeAssistant = Depends(hass)) -> None:
    """Test we setup the dependencies of a platform."""
    mock_integration(
        hass, MockModule("test_component", dependencies=["test_component2"])
    )
    mock_integration(hass, MockModule("test_component2"))
    mock_platform(hass, "test_component.test_domain", MockPlatform())

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    await component.async_setup({DOMAIN: {"platform": "test_component"}})
    await hass.async_block_till_done()
    expect("test_component" in hass.config.components).to_be(True)
    expect("test_component2" in hass.config.components).to_be(True)
    expect("test_component.test_domain" in hass.config.components).to_be(True)


@test
async def setup_entry(hass: HomeAssistant = Depends(hass)) -> None:
    """Test setup entry calls async_setup_entry on platform."""
    mock_setup_entry = AsyncMock(return_value=True)
    mock_platform(
        hass,
        "entry_domain.test_domain",
        MockPlatform(
            async_setup_entry=mock_setup_entry, scan_interval=timedelta(seconds=5)
        ),
    )

    component = EntityComponent(_LOGGER, DOMAIN, hass)
    entry = MockConfigEntry(domain="entry_domain")

    expect(await component.async_setup_entry(entry)).to_be_truthy()
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    p_hass, p_entry, _ = mock_setup_entry.mock_calls[0][1]
    expect(p_hass).to_be(hass)
    expect(p_entry).to_be(entry)

    expect(component._platforms[entry.entry_id].scan_interval).to_equal(
        timedelta(seconds=5)
    )


@test
async def setup_entry_platform_not_exist(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test setup entry fails if platform does not exist."""
    component = EntityComponent(_LOGGER, DOMAIN, hass)
    entry = MockConfigEntry(domain="non_existing")

    expect(await component.async_setup_entry(entry)).to_be(False)


@test
async def setup_entry_fails_duplicate(hass: HomeAssistant = Depends(hass)) -> None:
    """Test we don't allow setting up a config entry twice."""
    mock_setup_entry = AsyncMock(return_value=True)
    mock_platform(
        hass,
        "entry_domain.test_domain",
        MockPlatform(async_setup_entry=mock_setup_entry),
    )

    component = EntityComponent(_LOGGER, DOMAIN, hass)
    entry = MockConfigEntry(domain="entry_domain")

    expect(await component.async_setup_entry(entry)).to_be_truthy()

    expected_msg = re.escape(
        f"Config entry Mock Title ({entry.entry_id}) for "
        "entry_domain.test_domain has already been setup!"
    )
    try:
        await component.async_setup_entry(entry)
    except ValueError as err:
        expect(re.search(expected_msg, str(err))).not_.to_be_none()
        return
    raise AssertionError("Expected ValueError")


@test
async def unload_entry_resets_platform(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test unloading an entry removes all entities."""
    mock_setup_entry = AsyncMock(return_value=True)
    mock_platform(
        hass,
        "entry_domain.test_domain",
        MockPlatform(async_setup_entry=mock_setup_entry),
    )

    component = EntityComponent(_LOGGER, DOMAIN, hass)
    entry = MockConfigEntry(domain="entry_domain")

    expect(await component.async_setup_entry(entry)).to_be_truthy()
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    add_entities = mock_setup_entry.mock_calls[0][1][2]
    add_entities([MockEntity()])
    await hass.async_block_till_done()

    expect(len(hass.states.async_entity_ids())).to_equal(1)

    expect(await component.async_unload_entry(entry)).to_be_truthy()
    expect(len(hass.states.async_entity_ids())).to_equal(0)


@test
async def unload_entry_fails_if_never_loaded(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Unloading a never-loaded entry raises."""
    component = EntityComponent(_LOGGER, DOMAIN, hass)
    entry = MockConfigEntry(domain="entry_domain")

    try:
        await component.async_unload_entry(entry)
    except ValueError:
        return
    raise AssertionError("Expected ValueError")


@test
async def update_entity(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that we can update an entity with the helper."""
    component = EntityComponent(_LOGGER, DOMAIN, hass)
    await component.async_setup({})
    entity = MockEntity()
    entity.async_write_ha_state = Mock()
    entity.async_update_ha_state = AsyncMock(return_value=None)
    await component.async_add_entities([entity])

    expect(len(entity.async_write_ha_state.mock_calls)).to_equal(1)

    await async_update_entity(hass, entity.entity_id)

    expect(len(entity.async_update_ha_state.mock_calls)).to_equal(1)
    expect(entity.async_update_ha_state.mock_calls[-1][1][0]).to_be(True)


@test
async def set_service_race(hass: HomeAssistant = Depends(hass)) -> None:
    """Test race condition on setting service."""
    exception = False

    def async_loop_exception_handler(_, _2) -> None:
        nonlocal exception
        exception = True

    hass.loop.set_exception_handler(async_loop_exception_handler)

    await async_setup_component(hass, "group", {})
    component = EntityComponent(_LOGGER, DOMAIN, hass)
    await component.async_setup({})

    for _ in range(2):
        hass.async_create_task(component.async_add_entities([MockEntity()]))

    await hass.async_block_till_done()
    expect(exception).to_be(False)


@test
async def extract_all_omit_entity_id(hass: HomeAssistant = Depends(hass)) -> None:
    """Test extract all with None and *."""
    component = EntityComponent(_LOGGER, DOMAIN, hass)
    await component.async_setup({})
    await component.async_add_entities(
        [MockEntity(name="test_1"), MockEntity(name="test_2")]
    )

    call = ServiceCall(hass, "test", "service")

    expect(
        sorted(
            ent.entity_id for ent in await component.async_extract_from_service(call)
        )
    ).to_equal([])


@test
async def extract_all_use_match_all(hass: HomeAssistant = Depends(hass)) -> None:
    """Test extract all with None and *."""
    component = EntityComponent(_LOGGER, DOMAIN, hass)
    await component.async_setup({})
    await component.async_add_entities(
        [MockEntity(name="test_1"), MockEntity(name="test_2")]
    )

    call = ServiceCall(hass, "test", "service", {"entity_id": "all"})

    expect(
        sorted(
            ent.entity_id for ent in await component.async_extract_from_service(call)
        )
    ).to_equal(["test_domain.test_1", "test_domain.test_2"])


@test.cases(
    test.case("schema_str", schema={"some": str}, service_data={"some": "data"}),
    test.case("schema_empty", schema={}, service_data={}),
    test.case("schema_none", schema=None, service_data={}),
)
async def register_entity_service(
    schema: dict | None,
    service_data: dict,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test registering an entity service and calling it."""
    entity = MockEntity(entity_id=f"{DOMAIN}.entity")
    calls = []

    @callback
    def appender(**kwargs):
        calls.append(kwargs)

    entity.async_called_by_service = appender

    component = EntityComponent(_LOGGER, DOMAIN, hass)
    await component.async_setup({})
    await component.async_add_entities([entity])

    component.async_register_entity_service(
        "hello",
        schema,
        "async_called_by_service",
        description_placeholders={"test_placeholder": "beer"},
    )
    descriptions = await async_get_all_descriptions(hass)
    expect(descriptions["test_domain"]["hello"]["description_placeholders"]).to_equal(
        {"test_placeholder": "beer"}
    )

    async def _bad_call() -> None:
        await hass.services.async_call(
            DOMAIN,
            "hello",
            {"entity_id": entity.entity_id, "invalid": "data"},
            blocking=True,
        )

    try:
        await _bad_call()
    except vol.Invalid:
        pass
    else:
        raise AssertionError("Expected vol.Invalid")
    expect(len(calls)).to_equal(0)

    await hass.services.async_call(
        DOMAIN, "hello", {"entity_id": entity.entity_id} | service_data, blocking=True
    )
    expect(len(calls)).to_equal(1)
    expect(calls[0]).to_equal(service_data)

    await hass.services.async_call(
        DOMAIN, "hello", {"entity_id": ENTITY_MATCH_ALL} | service_data, blocking=True
    )
    expect(len(calls)).to_equal(2)
    expect(calls[1]).to_equal(service_data)

    await hass.services.async_call(
        DOMAIN, "hello", {"entity_id": ENTITY_MATCH_NONE} | service_data, blocking=True
    )
    expect(len(calls)).to_equal(2)

    await hass.services.async_call(
        DOMAIN, "hello", {"area_id": ENTITY_MATCH_NONE} | service_data, blocking=True
    )
    expect(len(calls)).to_equal(2)


@test
async def register_entity_service_response_data(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test an entity service that does support response data."""
    entity = MockEntity(entity_id=f"{DOMAIN}.entity")

    async def generate_response(
        target: MockEntity, call: ServiceCall
    ) -> ServiceResponse:
        expect(call.return_response).to_be(True)
        return {"response-key": "response-value"}

    component = EntityComponent(_LOGGER, DOMAIN, hass)
    await component.async_setup({})
    await component.async_add_entities([entity])

    component.async_register_entity_service(
        "hello",
        {"some": str},
        generate_response,
        supports_response=SupportsResponse.ONLY,
    )

    response_data = await hass.services.async_call(
        DOMAIN,
        "hello",
        service_data={"some": "data"},
        target={"entity_id": [entity.entity_id]},
        blocking=True,
        return_response=True,
    )
    expect(response_data).to_equal(
        {f"{DOMAIN}.entity": {"response-key": "response-value"}}
    )


@test
async def register_entity_service_response_data_multiple_matches(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test asking for service response data and matching many entities."""
    entity1 = MockEntity(entity_id=f"{DOMAIN}.entity1")
    entity2 = MockEntity(entity_id=f"{DOMAIN}.entity2")

    async def generate_response(
        target: MockEntity, call: ServiceCall
    ) -> ServiceResponse:
        return {"response-key": f"response-value-{target.entity_id}"}

    component = EntityComponent(_LOGGER, DOMAIN, hass)
    await component.async_setup({})
    await component.async_add_entities([entity1, entity2])

    component.async_register_entity_service(
        "hello",
        {"some": str},
        generate_response,
        supports_response=SupportsResponse.ONLY,
    )

    response_data = await hass.services.async_call(
        DOMAIN,
        "hello",
        service_data={"some": "data"},
        target={"entity_id": [entity1.entity_id, entity2.entity_id]},
        blocking=True,
        return_response=True,
    )
    expect(response_data).to_equal(
        {
            f"{DOMAIN}.entity1": {"response-key": f"response-value-{DOMAIN}.entity1"},
            f"{DOMAIN}.entity2": {"response-key": f"response-value-{DOMAIN}.entity2"},
        }
    )


@test
async def register_entity_service_response_data_multiple_matches_raises(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test asking for service response data and matching many entities raises exceptions."""
    entity1 = MockEntity(entity_id=f"{DOMAIN}.entity1")
    entity2 = MockEntity(entity_id=f"{DOMAIN}.entity2")

    async def generate_response(
        target: MockEntity, call: ServiceCall
    ) -> ServiceResponse:
        if target.entity_id == f"{DOMAIN}.entity1":
            raise RuntimeError("Something went wrong")
        return {"response-key": f"response-value-{target.entity_id}"}

    component = EntityComponent(_LOGGER, DOMAIN, hass)
    await component.async_setup({})
    await component.async_add_entities([entity1, entity2])

    component.async_register_entity_service(
        "hello",
        {"some": str},
        generate_response,
        supports_response=SupportsResponse.ONLY,
    )

    try:
        await hass.services.async_call(
            DOMAIN,
            "hello",
            service_data={"some": "data"},
            target={"entity_id": [entity1.entity_id, entity2.entity_id]},
            blocking=True,
            return_response=True,
        )
    except RuntimeError as err:
        expect(str(err)).to_contain("Something went wrong")
        return
    raise AssertionError("Expected RuntimeError")


@test
async def register_batched_entity_service(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test registering a batched entity service and calling it."""
    entity1 = MockEntity(entity_id=f"{DOMAIN}.entity1")
    entity2 = MockEntity(entity_id=f"{DOMAIN}.entity2")

    calls: list[tuple[list[MockEntity], ServiceCall]] = []

    async def handle_service(entities: list[MockEntity], call: ServiceCall) -> None:
        calls.append((entities, call))

    component = EntityComponent(_LOGGER, DOMAIN, hass)
    await component.async_setup({})
    await component.async_add_entities([entity1, entity2])

    component.async_register_batched_entity_service(
        "hello",
        {"some": str},
        handle_service,
        description_placeholders={"test_placeholder": "beer"},
    )
    descriptions = await async_get_all_descriptions(hass)
    expect(descriptions[DOMAIN]["hello"]["description_placeholders"]).to_equal(
        {"test_placeholder": "beer"}
    )

    try:
        await hass.services.async_call(
            DOMAIN,
            "hello",
            {"entity_id": entity1.entity_id, "invalid": "data"},
            blocking=True,
        )
    except vol.Invalid:
        pass
    else:
        raise AssertionError("Expected vol.Invalid")
    expect(len(calls)).to_equal(0)

    await hass.services.async_call(
        DOMAIN,
        "hello",
        {"entity_id": entity1.entity_id, "some": "data"},
        blocking=True,
    )
    expect(len(calls)).to_equal(1)
    expect(calls[0][0]).to_equal([entity1])
    expect(calls[0][1].data).to_equal({"some": "data"})

    await hass.services.async_call(
        DOMAIN,
        "hello",
        {"entity_id": ENTITY_MATCH_ALL, "some": "data"},
        blocking=True,
    )
    expect(len(calls)).to_equal(2)
    expect(calls[1][0]).to_equal(unordered([entity1, entity2]))

    await hass.services.async_call(
        DOMAIN,
        "hello",
        {"entity_id": ENTITY_MATCH_NONE, "some": "data"},
        blocking=True,
    )
    expect(len(calls)).to_equal(2)


@test
async def register_batched_entity_service_response_data(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test a batched entity service that supports response data."""
    entity1 = MockEntity(entity_id=f"{DOMAIN}.entity1")
    entity2 = MockEntity(entity_id=f"{DOMAIN}.entity2")

    async def handle_service(
        entities: list[MockEntity], call: ServiceCall
    ) -> EntityServiceResponse:
        expect(call.return_response).to_be(True)
        return {
            e.entity_id: {"response-key": f"response-value-{e.entity_id}"}
            for e in entities
        }

    component = EntityComponent(_LOGGER, DOMAIN, hass)
    await component.async_setup({})
    await component.async_add_entities([entity1, entity2])

    component.async_register_batched_entity_service(
        "hello",
        {"some": str},
        handle_service,
        supports_response=SupportsResponse.ONLY,
    )

    response_data = await hass.services.async_call(
        DOMAIN,
        "hello",
        service_data={"some": "data"},
        target={"entity_id": [entity1.entity_id, entity2.entity_id]},
        blocking=True,
        return_response=True,
    )
    expect(response_data).to_equal(
        {
            f"{DOMAIN}.entity1": {"response-key": f"response-value-{DOMAIN}.entity1"},
            f"{DOMAIN}.entity2": {"response-key": f"response-value-{DOMAIN}.entity2"},
        }
    )


@test
async def register_entity_service_non_entity_service_schema(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test attempting to register a service with a non entity service schema."""
    component = EntityComponent(_LOGGER, DOMAIN, hass)

    for idx, schema in enumerate(
        (
            vol.Schema({"some": str}),
            vol.All(vol.Schema({"some": str})),
            vol.Any(vol.Schema({"some": str})),
        )
    ):
        expected_message = (
            f"The test_domain.hello_{idx} service registers "
            "an entity service with a non entity service schema"
        )
        expect(
            lambda s=schema, i=idx: component.async_register_entity_service(
                f"hello_{i}", s, Mock()
            )
        ).to_raise(HomeAssistantError, match=expected_message)
        expect(
            lambda s=schema, i=idx: component.async_register_batched_entity_service(
                f"hello_{i}", s, AsyncMock()
            )
        ).to_raise(HomeAssistantError, match=expected_message)

    for idx, schema in enumerate(
        (
            cv.make_entity_service_schema({"some": str}),
            vol.Schema(cv.make_entity_service_schema({"some": str})),
            vol.All(cv.make_entity_service_schema({"some": str})),
        )
    ):
        component.async_register_entity_service(f"test_service_{idx}", schema, Mock())
        component.async_register_batched_entity_service(
            f"test_service_batched_{idx}", schema, AsyncMock()
        )


@test
async def platforms_shutdown_on_stop(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test that we shutdown platforms on stop."""
    platform1_setup = Mock(side_effect=[PlatformNotReady, PlatformNotReady, None])
    mock_integration(hass, MockModule("mod1"))
    mock_platform(
        hass, "mod1.test_domain", MockPlatform(setup_platform=platform1_setup)
    )

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    await component.async_setup({DOMAIN: {"platform": "mod1"}})
    await hass.async_block_till_done()
    expect(len(platform1_setup.mock_calls)).to_equal(1)
    expect("mod1.test_domain" in hass.config.components).to_be(False)

    with patch.object(
        component._platforms[DOMAIN], "async_shutdown"
    ) as mock_async_shutdown:
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
        await hass.async_block_till_done()

    expect(mock_async_shutdown.called).to_be(True)
