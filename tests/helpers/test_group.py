"""Test the group helper."""

from tryke import Depends, expect, fixture, test

from homeassistant.const import ATTR_ENTITY_ID, ATTR_GROUP_ENTITIES, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, group
from homeassistant.helpers.group import (
    GenericGroup,
    IntegrationSpecificGroup,
    get_group_entities,
)

from tests.common import MockEntity, MockEntityPlatform
from tests.hass_fixtures import entity_registry, hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def expand_entity_ids(hass: HomeAssistant = Depends(hass)) -> None:
    """Test expand_entity_ids method."""
    hass.states.async_set("light.Bowl", STATE_ON)
    hass.states.async_set("light.Ceiling", STATE_OFF)
    hass.states.async_set(
        "group.init_group", STATE_ON, {ATTR_ENTITY_ID: ["light.bowl", "light.ceiling"]}
    )
    state = hass.states.get("group.init_group")
    expect(state).not_.to_be_none()
    expect(state.attributes[ATTR_ENTITY_ID]).to_equal(["light.bowl", "light.ceiling"])

    expect(sorted(group.expand_entity_ids(hass, ["group.init_group"]))).to_equal(
        ["light.bowl", "light.ceiling"]
    )
    expect(sorted(group.expand_entity_ids(hass, ["group.INIT_group"]))).to_equal(
        ["light.bowl", "light.ceiling"]
    )


@test
async def expand_entity_ids_does_not_return_duplicates(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test that expand_entity_ids does not return duplicates."""
    hass.states.async_set("light.Bowl", STATE_ON)
    hass.states.async_set("light.Ceiling", STATE_OFF)
    hass.states.async_set(
        "group.init_group", STATE_ON, {ATTR_ENTITY_ID: ["light.bowl", "light.ceiling"]}
    )

    expect(
        sorted(group.expand_entity_ids(hass, ["group.init_group", "light.Ceiling"]))
    ).to_equal(["light.bowl", "light.ceiling"])

    expect(
        sorted(group.expand_entity_ids(hass, ["light.bowl", "group.init_group"]))
    ).to_equal(["light.bowl", "light.ceiling"])


@test
async def expand_entity_ids_recursive(hass: HomeAssistant = Depends(hass)) -> None:
    """Test expand_entity_ids method with a group that contains itself."""
    hass.states.async_set("light.Bowl", STATE_ON)
    hass.states.async_set("light.Ceiling", STATE_OFF)
    hass.states.async_set(
        "group.init_group", STATE_ON, {ATTR_ENTITY_ID: ["light.bowl", "light.ceiling"]}
    )

    hass.states.async_set(
        "group.rec_group",
        STATE_ON,
        {ATTR_ENTITY_ID: ["group.init_group", "light.ceiling"]},
    )

    expect(sorted(group.expand_entity_ids(hass, ["group.rec_group"]))).to_equal(
        ["light.bowl", "light.ceiling"]
    )


@test
async def expand_entity_ids_ignores_non_strings(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test that non string elements in lists are ignored."""
    expect(group.expand_entity_ids(hass, [5, True])).to_equal([])


@test
async def get_entity_ids(hass: HomeAssistant = Depends(hass)) -> None:
    """Test get_entity_ids method."""
    hass.states.async_set("light.Bowl", STATE_ON)
    hass.states.async_set("light.Ceiling", STATE_OFF)
    hass.states.async_set(
        "group.init_group", STATE_ON, {ATTR_ENTITY_ID: ["light.bowl", "light.ceiling"]}
    )

    expect(sorted(group.get_entity_ids(hass, "group.init_group"))).to_equal(
        ["light.bowl", "light.ceiling"]
    )


@test
async def get_entity_ids_with_domain_filter(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test if get_entity_ids works with a domain_filter."""
    hass.states.async_set("switch.AC", STATE_OFF)
    hass.states.async_set(
        "group.mixed_group", STATE_ON, {ATTR_ENTITY_ID: ["light.bowl", "switch.ac"]}
    )

    expect(
        group.get_entity_ids(hass, "group.mixed_group", domain_filter="switch")
    ).to_equal(["switch.ac"])


@test
async def get_entity_ids_with_non_existing_group_name(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test get_entity_ids with a non existing group."""
    expect(group.get_entity_ids(hass, "non_existing")).to_equal([])


@test
async def get_entity_ids_with_non_group_state(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test get_entity_ids with a non group state."""
    expect(group.get_entity_ids(hass, "switch.AC")).to_equal([])


@test
async def get_group_entities_(hass: HomeAssistant = Depends(hass)) -> None:
    """Test get_group_entities returns registered group entities."""
    expect(get_group_entities(hass)).to_equal({})

    platform = MockEntityPlatform(hass, domain="light", platform_name="test")

    ent = MockEntity(entity_id="light.test_group", unique_id="test_group")
    ent.group = GenericGroup(ent, ["light.bulb1", "light.bulb2"])

    await platform.async_add_entities([ent])
    await hass.async_block_till_done()

    group_entities = get_group_entities(hass)
    expect("light.test_group" in group_entities).to_be(True)
    expect(group_entities["light.test_group"] is ent).to_be(True)


@test
async def group_entity_removed_from_registry(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test group entity is removed from get_group_entities on removal."""
    platform = MockEntityPlatform(hass, domain="light", platform_name="test")

    ent = MockEntity(entity_id="light.test_group", unique_id="test_group")
    ent.group = GenericGroup(ent, ["light.bulb1", "light.bulb2"])

    await platform.async_add_entities([ent])
    await hass.async_block_till_done()
    expect("light.test_group" in get_group_entities(hass)).to_be(True)

    await platform.async_remove_entity(ent.entity_id)
    await hass.async_block_till_done()
    expect("light.test_group" not in get_group_entities(hass)).to_be(True)


@test
async def group_entity_id_changed_in_registry(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test get_group_entities reflects new key when group entity ID is changed."""
    platform = MockEntityPlatform(hass, domain="light", platform_name="test")

    ent = MockEntity(entity_id="light.old_id", unique_id="test_group")
    ent.group = GenericGroup(ent, ["light.bulb1", "light.bulb2"])

    await platform.async_add_entities([ent])
    await hass.async_block_till_done()

    expect("light.old_id" in get_group_entities(hass)).to_be(True)

    entity_registry.async_update_entity("light.old_id", new_entity_id="light.new_id")
    await hass.async_block_till_done()

    group_entities = get_group_entities(hass)
    expect("light.old_id" not in group_entities).to_be(True)
    expect("light.new_id" in group_entities).to_be(True)

    expanded = group.expand_entity_ids(hass, ["light.new_id"])
    expect(sorted(expanded)).to_equal(["light.bulb1", "light.bulb2"])


@test
async def multiple_group_entities(hass: HomeAssistant = Depends(hass)) -> None:
    """Test multiple group entities can be registered and work independently."""
    platform = MockEntityPlatform(hass, domain="light", platform_name="test")

    ent1 = MockEntity(entity_id="light.group1", unique_id="multi_1")
    ent1.group = GenericGroup(ent1, ["light.a", "light.b"])

    ent2 = MockEntity(entity_id="light.group2", unique_id="multi_2")
    ent2.group = GenericGroup(ent2, ["light.c", "light.d"])

    await platform.async_add_entities([ent1, ent2])
    await hass.async_block_till_done()

    group_entities = get_group_entities(hass)
    expect("light.group1" in group_entities).to_be(True)
    expect("light.group2" in group_entities).to_be(True)

    expanded1 = group.expand_entity_ids(hass, ["light.group1"])
    expanded2 = group.expand_entity_ids(hass, ["light.group2"])

    expect(sorted(expanded1)).to_equal(["light.a", "light.b"])
    expect(sorted(expanded2)).to_equal(["light.c", "light.d"])


@test
async def generic_group_member_entity_ids(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test GenericGroup member_entity_ids property."""
    platform = MockEntityPlatform(hass, domain="light", platform_name="test")

    ent = MockEntity(entity_id="light.test_group")
    ent.group = GenericGroup(ent, ["light.bulb1", "light.bulb2"])

    await platform.async_add_entities([ent])
    await hass.async_block_till_done()

    expect(ent.group.member_entity_ids).to_equal(["light.bulb1", "light.bulb2"])


@test
async def expand_entity_ids_with_generic_group(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test expand_entity_ids with GenericGroup entities."""
    platform = MockEntityPlatform(hass, domain="light", platform_name="test")

    ent = MockEntity(entity_id="light.living_room_group", unique_id="living_room")
    ent.group = GenericGroup(ent, ["light.lamp1", "light.lamp2", "light.lamp3"])

    await platform.async_add_entities([ent])
    await hass.async_block_till_done()

    hass.states.async_set("light.lamp1", STATE_ON)
    hass.states.async_set("light.lamp2", STATE_OFF)
    hass.states.async_set("light.lamp3", STATE_ON)

    expanded = group.expand_entity_ids(hass, ["light.living_room_group"])
    expect(sorted(expanded)).to_equal(["light.lamp1", "light.lamp2", "light.lamp3"])


@test
async def expand_entity_ids_with_generic_group_recursive(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test expand_entity_ids with nested GenericGroup entities."""
    platform = MockEntityPlatform(hass, domain="light", platform_name="test")

    inner_group = MockEntity(entity_id="light.inner_group", unique_id="inner")
    inner_group.group = GenericGroup(inner_group, ["light.lamp1", "light.lamp2"])

    outer_group = MockEntity(entity_id="light.outer_group", unique_id="outer")
    outer_group.group = GenericGroup(outer_group, ["light.inner_group", "light.lamp3"])

    await platform.async_add_entities([inner_group, outer_group])
    await hass.async_block_till_done()

    expanded = group.expand_entity_ids(hass, ["light.outer_group"])
    expect(sorted(expanded)).to_equal(["light.lamp1", "light.lamp2", "light.lamp3"])


@test
async def expand_entity_ids_with_generic_group_self_reference(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test expand_entity_ids handles GenericGroup with self-reference."""
    platform = MockEntityPlatform(hass, domain="light", platform_name="test")

    ent = MockEntity(entity_id="light.self_ref_group", unique_id="self_ref")
    ent.group = GenericGroup(
        ent, ["light.self_ref_group", "light.bulb1", "light.bulb2"]
    )

    await platform.async_add_entities([ent])
    await hass.async_block_till_done()

    expanded = group.expand_entity_ids(hass, ["light.self_ref_group"])
    expect(sorted(expanded)).to_equal(["light.bulb1", "light.bulb2"])


@test
async def generic_group_attribute_in_state(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test ATTR_GROUP_ENTITIES is included in GenericGroup state."""
    platform = MockEntityPlatform(hass, domain="light", platform_name="test")

    ent = MockEntity(entity_id="light.group_with_attrs", unique_id="attrs_test")
    ent.group = GenericGroup(ent, ["light.lamp1", "light.lamp2"])

    await platform.async_add_entities([ent])
    await hass.async_block_till_done()

    state = hass.states.get("light.group_with_attrs")
    expect(state).not_.to_be_none()
    expect(ATTR_GROUP_ENTITIES in state.attributes).to_be(True)
    expect(state.attributes[ATTR_GROUP_ENTITIES]).to_equal(
        ["light.lamp1", "light.lamp2"]
    )


@test
async def integration_specific_group_member_entity_ids(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test IntegrationSpecificGroup resolves entity IDs from unique IDs."""
    entity_registry.async_get_or_create(
        "light", "test", "unique_1", suggested_object_id="member1"
    )
    entity_registry.async_get_or_create(
        "light", "test", "unique_2", suggested_object_id="member2"
    )

    platform = MockEntityPlatform(hass, domain="light", platform_name="test")

    ent = MockEntity(entity_id="light.integration_group", unique_id="int_group")
    ent.group = IntegrationSpecificGroup(ent, ["unique_1", "unique_2"])

    await platform.async_add_entities([ent])
    await hass.async_block_till_done()

    expect(sorted(ent.group.member_entity_ids)).to_equal(
        ["light.member1", "light.member2"]
    )


@test
async def integration_specific_group_missing_entities(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test IntegrationSpecificGroup handles missing entities."""
    entity_registry.async_get_or_create(
        "light", "test", "unique_1", suggested_object_id="member1"
    )

    platform = MockEntityPlatform(hass, domain="light", platform_name="test")

    ent = MockEntity(entity_id="light.partial_group", unique_id="partial")
    ent.group = IntegrationSpecificGroup(
        ent, ["unique_1", "unique_2", "unique_missing"]
    )

    await platform.async_add_entities([ent])
    await hass.async_block_till_done()

    expect(ent.group.member_entity_ids).to_equal(["light.member1"])


@test
async def integration_specific_group_member_unique_ids_setter(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test IntegrationSpecificGroup member_unique_ids setter clears cache."""
    entity_registry.async_get_or_create(
        "light", "test", "unique_1", suggested_object_id="member1"
    )
    entity_registry.async_get_or_create(
        "light", "test", "unique_2", suggested_object_id="member2"
    )
    entity_registry.async_get_or_create(
        "light", "test", "unique_3", suggested_object_id="member3"
    )

    platform = MockEntityPlatform(hass, domain="light", platform_name="test")

    ent = MockEntity(entity_id="light.dynamic_group", unique_id="dynamic")
    ent.group = IntegrationSpecificGroup(ent, ["unique_1"])

    await platform.async_add_entities([ent])
    await hass.async_block_till_done()
    expect(ent.group.member_entity_ids).to_equal(["light.member1"])

    ent.group.member_unique_ids = ["unique_2", "unique_3"]

    expect(sorted(ent.group.member_entity_ids)).to_equal(
        ["light.member2", "light.member3"]
    )


@test
async def integration_specific_group_member_added(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test IntegrationSpecificGroup updates when member is added to registry."""
    entity_registry.async_get_or_create(
        "light", "test", "unique_1", suggested_object_id="member1"
    )

    platform = MockEntityPlatform(hass, domain="light", platform_name="test")

    ent = MockEntity(entity_id="light.registry_group", unique_id="reg_group")
    ent.group = IntegrationSpecificGroup(ent, ["unique_1", "unique_2"])

    await platform.async_add_entities([ent])
    await hass.async_block_till_done()
    expect(ent.group.member_entity_ids).to_equal(["light.member1"])

    entity_registry.async_get_or_create(
        "light", "test", "unique_2", suggested_object_id="member2"
    )
    await hass.async_block_till_done()

    expect(sorted(ent.group.member_entity_ids)).to_equal(
        ["light.member1", "light.member2"]
    )


@test
async def integration_specific_group_member_removed(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test IntegrationSpecificGroup updates when member is removed from registry."""
    entry1 = entity_registry.async_get_or_create(
        "light", "test", "unique_1", suggested_object_id="member1"
    )
    entity_registry.async_get_or_create(
        "light", "test", "unique_2", suggested_object_id="member2"
    )

    platform = MockEntityPlatform(hass, domain="light", platform_name="test")

    ent = MockEntity(entity_id="light.remove_group", unique_id="rem_group")
    ent.group = IntegrationSpecificGroup(ent, ["unique_1", "unique_2"])

    await platform.async_add_entities([ent])
    await hass.async_block_till_done()

    expect(sorted(ent.group.member_entity_ids)).to_equal(
        ["light.member1", "light.member2"]
    )

    entity_registry.async_remove(entry1.entity_id)
    await hass.async_block_till_done()

    expect(ent.group.member_entity_ids).to_equal(["light.member2"])


@test
async def integration_specific_group_member_renamed(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test IntegrationSpecificGroup updates when member entity_id is renamed."""
    entry = entity_registry.async_get_or_create(
        "light", "test", "unique_1", suggested_object_id="original_name"
    )

    platform = MockEntityPlatform(hass, domain="light", platform_name="test")

    ent = MockEntity(entity_id="light.group", unique_id="grp")
    ent.group = IntegrationSpecificGroup(ent, ["unique_1"])

    await platform.async_add_entities([ent])
    await hass.async_block_till_done()
    expect(ent.group.member_entity_ids).to_equal(["light.original_name"])

    entity_registry.async_update_entity(entry.entity_id, new_entity_id="light.new_id")
    await hass.async_block_till_done()

    expect(ent.group.member_entity_ids).to_equal(["light.new_id"])


@test
async def integration_specific_group_attribute_in_state(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test ATTR_GROUP_ENTITIES is included in IntegrationSpecificGroup state."""
    entity_registry.async_get_or_create(
        "light", "test", "unique_1", suggested_object_id="member1"
    )
    entity_registry.async_get_or_create(
        "light", "test", "unique_2", suggested_object_id="member2"
    )

    platform = MockEntityPlatform(hass, domain="light", platform_name="test")

    ent = MockEntity(entity_id="light.int_group_attrs", unique_id="int_attrs")
    ent.group = IntegrationSpecificGroup(ent, ["unique_1", "unique_2"])

    await platform.async_add_entities([ent])
    await hass.async_block_till_done()

    state = hass.states.get("light.int_group_attrs")
    expect(state).not_.to_be_none()
    expect(ATTR_GROUP_ENTITIES in state.attributes).to_be(True)
    expect(sorted(state.attributes[ATTR_GROUP_ENTITIES])).to_equal(
        ["light.member1", "light.member2"]
    )


@test
async def expand_entity_ids_integration_specific_group_not_expanded(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test expand_entity_ids doesn't expand IntegrationSpecificGroup."""
    entity_registry.async_get_or_create(
        "light", "test", "unique_1", suggested_object_id="member1"
    )
    entity_registry.async_get_or_create(
        "light", "test", "unique_2", suggested_object_id="member2"
    )

    platform = MockEntityPlatform(hass, domain="light", platform_name="test")

    ent = MockEntity(entity_id="light.int_specific_group", unique_id="int_spec")
    ent.group = IntegrationSpecificGroup(ent, ["unique_1", "unique_2"])

    await platform.async_add_entities([ent])
    await hass.async_block_till_done()

    expanded = group.expand_entity_ids(hass, ["light.int_specific_group"])
    expect(expanded).to_equal(["light.int_specific_group"])
