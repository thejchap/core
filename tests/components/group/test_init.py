"""The tests for the Group components (tryke port)."""

from tryke import Depends, expect, fixture, test

from homeassistant.components import group
from homeassistant.const import STATE_HOME, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke fixture resolution and set up the homeassistant integration.

    The pytest conftest.py autouse fixture ``setup_homeassistant`` does not
    run under tryke, so we install the ``homeassistant`` component here.
    """
    expect(await async_setup_component(hass, "homeassistant", {})).to_be_truthy()
    return hass


@test
def domain_const_importable() -> None:
    """Smoke test: the group integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.group.const import DOMAIN  # noqa: PLC0415

    expect(DOMAIN).to_equal("group")


@test
async def setup_group_with_mixed_groupable_states(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Try to set up a group with mixed groupable states."""
    hass.states.async_set("light.Bowl", STATE_ON)
    hass.states.async_set("device_tracker.Paulus", STATE_HOME)

    expect(await async_setup_component(hass, "group", {})).to_be_truthy()

    await group.Group.async_create_group(
        hass,
        "person_and_light",
        created_by_service=False,
        entity_ids=["light.Bowl", "device_tracker.Paulus"],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )

    await hass.async_block_till_done()

    expect(hass.states.get(f"{group.DOMAIN}.person_and_light").state).to_equal(
        STATE_ON
    )


@test
async def setup_group_with_a_non_existing_state(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Try to set up a group with a non existing state."""
    hass.states.async_set("light.Bowl", STATE_ON)

    expect(await async_setup_component(hass, "group", {})).to_be_truthy()

    grp = await group.Group.async_create_group(
        hass,
        "light_and_nothing",
        created_by_service=False,
        entity_ids=["light.Bowl", "non.existing"],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )

    expect(grp.state).to_equal(STATE_ON)


@test
async def setup_group_with_non_groupable_states(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setup with groups which are not groupable."""
    hass.states.async_set("cast.living_room", "Plex")
    hass.states.async_set("cast.bedroom", "Netflix")

    expect(await async_setup_component(hass, "group", {})).to_be_truthy()

    grp = await group.Group.async_create_group(
        hass,
        "chromecasts",
        created_by_service=False,
        entity_ids=["cast.living_room", "cast.bedroom"],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )

    expect(grp.state).to_be(None)


@test
async def setup_empty_group(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Try to set up an empty group."""
    expect(await async_setup_component(hass, "group", {})).to_be_truthy()

    grp = await group.Group.async_create_group(
        hass,
        "nothing",
        created_by_service=False,
        entity_ids=[],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )

    expect(grp.state).to_be(None)


@test
async def monitor_group(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test if the group keeps track of states."""
    hass.states.async_set("light.Bowl", STATE_ON)
    hass.states.async_set("light.Ceiling", STATE_OFF)

    expect(await async_setup_component(hass, "group", {})).to_be_truthy()

    test_group = await group.Group.async_create_group(
        hass,
        "init_group",
        created_by_service=True,
        entity_ids=["light.Bowl", "light.Ceiling"],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )

    expect(test_group.entity_id in hass.states.async_entity_ids()).to_be(True)

    group_state = hass.states.get(test_group.entity_id)
    expect(group_state.state).to_equal(STATE_ON)
    expect(bool(group_state.attributes.get(group.ATTR_AUTO))).to_be(True)


@test
async def group_turns_off_if_all_off(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test if turn off if the last device that was on turns off."""
    hass.states.async_set("light.Bowl", STATE_OFF)
    hass.states.async_set("light.Ceiling", STATE_OFF)

    expect(await async_setup_component(hass, "group", {})).to_be_truthy()

    test_group = await group.Group.async_create_group(
        hass,
        "init_group",
        created_by_service=True,
        entity_ids=["light.Bowl", "light.Ceiling"],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )

    await hass.async_block_till_done()

    group_state = hass.states.get(test_group.entity_id)
    expect(group_state.state).to_equal(STATE_OFF)


@test
async def group_turns_on_if_all_are_off_and_one_turns_on(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test if turn on if all devices were turned off and one turns on."""
    hass.states.async_set("light.Bowl", STATE_OFF)
    hass.states.async_set("light.Ceiling", STATE_OFF)

    expect(await async_setup_component(hass, "group", {})).to_be_truthy()

    test_group = await group.Group.async_create_group(
        hass,
        "init_group",
        created_by_service=True,
        entity_ids=["light.Bowl", "light.Ceiling"],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )

    hass.states.async_set("light.Ceiling", STATE_ON)
    await hass.async_block_till_done()

    group_state = hass.states.get(test_group.entity_id)
    expect(group_state.state).to_equal(STATE_ON)


@test
async def allgroup_stays_off_if_all_are_off_and_one_turns_on(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Group with all: true, stay off if one device turns on."""
    hass.states.async_set("light.Bowl", STATE_OFF)
    hass.states.async_set("light.Ceiling", STATE_OFF)

    expect(await async_setup_component(hass, "group", {})).to_be_truthy()

    test_group = await group.Group.async_create_group(
        hass,
        "init_group",
        created_by_service=True,
        entity_ids=["light.Bowl", "light.Ceiling"],
        icon=None,
        mode=True,
        object_id=None,
        order=None,
    )

    hass.states.async_set("light.Ceiling", STATE_ON)
    await hass.async_block_till_done()

    group_state = hass.states.get(test_group.entity_id)
    expect(group_state.state).to_equal(STATE_OFF)


@test
async def allgroup_turn_on_if_last_turns_on(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Group with all: true, turn on if all devices are on."""
    hass.states.async_set("light.Bowl", STATE_ON)
    hass.states.async_set("light.Ceiling", STATE_OFF)

    expect(await async_setup_component(hass, "group", {})).to_be_truthy()

    test_group = await group.Group.async_create_group(
        hass,
        "init_group",
        created_by_service=True,
        entity_ids=["light.Bowl", "light.Ceiling"],
        icon=None,
        mode=True,
        object_id=None,
        order=None,
    )

    hass.states.async_set("light.Ceiling", STATE_ON)
    await hass.async_block_till_done()

    group_state = hass.states.get(test_group.entity_id)
    expect(group_state.state).to_equal(STATE_ON)


@test
async def expand_entity_ids(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test expand_entity_ids method."""
    hass.states.async_set("light.Bowl", STATE_ON)
    hass.states.async_set("light.Ceiling", STATE_OFF)

    expect(await async_setup_component(hass, "group", {})).to_be_truthy()

    test_group = await group.Group.async_create_group(
        hass,
        "init_group",
        created_by_service=True,
        entity_ids=["light.Bowl", "light.Ceiling"],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )

    expect(sorted(group.expand_entity_ids(hass, [test_group.entity_id]))).to_equal(
        sorted(["light.ceiling", "light.bowl"])
    )


@test
async def expand_entity_ids_does_not_return_duplicates(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that expand_entity_ids does not return duplicates."""
    hass.states.async_set("light.Bowl", STATE_ON)
    hass.states.async_set("light.Ceiling", STATE_OFF)

    expect(await async_setup_component(hass, "group", {})).to_be_truthy()

    test_group = await group.Group.async_create_group(
        hass,
        "init_group",
        created_by_service=True,
        entity_ids=["light.Bowl", "light.Ceiling"],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )

    expect(
        sorted(group.expand_entity_ids(hass, [test_group.entity_id, "light.Ceiling"]))
    ).to_equal(["light.bowl", "light.ceiling"])

    expect(
        sorted(group.expand_entity_ids(hass, ["light.bowl", test_group.entity_id]))
    ).to_equal(["light.bowl", "light.ceiling"])


@test
async def expand_entity_ids_recursive(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test expand_entity_ids method with a group that contains itself."""
    hass.states.async_set("light.Bowl", STATE_ON)
    hass.states.async_set("light.Ceiling", STATE_OFF)

    expect(await async_setup_component(hass, "group", {})).to_be_truthy()

    test_group = await group.Group.async_create_group(
        hass,
        "init_group",
        created_by_service=True,
        entity_ids=["light.Bowl", "light.Ceiling", "group.init_group"],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )

    expect(sorted(group.expand_entity_ids(hass, [test_group.entity_id]))).to_equal(
        sorted(["light.ceiling", "light.bowl"])
    )


@test
async def expand_entity_ids_ignores_non_strings(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that non string elements in lists are ignored."""
    expect(group.expand_entity_ids(hass, [5, True])).to_equal([])


@test
async def get_entity_ids(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test get_entity_ids method."""
    hass.states.async_set("light.Bowl", STATE_ON)
    hass.states.async_set("light.Ceiling", STATE_OFF)

    expect(await async_setup_component(hass, "group", {})).to_be_truthy()

    test_group = await group.Group.async_create_group(
        hass,
        "init_group",
        created_by_service=True,
        entity_ids=["light.Bowl", "light.Ceiling"],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )

    expect(sorted(group.get_entity_ids(hass, test_group.entity_id))).to_equal(
        ["light.bowl", "light.ceiling"]
    )


@test
async def get_entity_ids_with_domain_filter(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test if get_entity_ids works with a domain_filter."""
    hass.states.async_set("switch.AC", STATE_OFF)

    expect(await async_setup_component(hass, "group", {})).to_be_truthy()

    mixed_group = await group.Group.async_create_group(
        hass,
        "mixed_group",
        created_by_service=True,
        entity_ids=["light.Bowl", "switch.AC"],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )

    expect(
        group.get_entity_ids(hass, mixed_group.entity_id, domain_filter="switch")
    ).to_equal(["switch.ac"])


@test
async def get_entity_ids_with_non_existing_group_name(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test get_entity_ids with a non existing group."""
    expect(group.get_entity_ids(hass, "non_existing")).to_equal([])


@test
async def get_entity_ids_with_non_group_state(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test get_entity_ids with a non group state."""
    expect(group.get_entity_ids(hass, "switch.AC")).to_equal([])


@test.skip("pending tryke port")
async def group_being_init_before_first_tracked_state_is_set_to_on() -> None:
    """Stub for test_group_being_init_before_first_tracked_state_is_set_to_on."""


@test.skip("pending tryke port")
async def group_being_init_before_first_tracked_state_is_set_to_off() -> None:
    """Stub for test_group_being_init_before_first_tracked_state_is_set_to_off."""


@test.skip("pending tryke port")
async def groups_get_unique_names() -> None:
    """Stub for test_groups_get_unique_names."""


@test.skip("pending tryke port")
async def expand_entity_ids_expands_nested_groups() -> None:
    """Stub for test_expand_entity_ids_expands_nested_groups."""


@test.skip("pending tryke port")
async def set_assumed_state_based_on_tracked() -> None:
    """Stub for test_set_assumed_state_based_on_tracked."""


@test.skip("pending tryke port")
async def group_updated_after_device_tracker_zone_change() -> None:
    """Stub for test_group_updated_after_device_tracker_zone_change."""


@test.skip("pending tryke port")
async def is_on() -> None:
    """Stub for test_is_on."""


@test.skip("pending tryke port")
async def is_on_and_state_mixed_domains() -> None:
    """Stub for test_is_on_and_state_mixed_domains."""


@test.skip("pending tryke port")
async def reloading_groups() -> None:
    """Stub for test_reloading_groups."""


@test.skip("pending tryke port")
async def modify_group() -> None:
    """Stub for test_modify_group."""


@test.skip("pending tryke port")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port")
async def service_group_services() -> None:
    """Stub for test_service_group_services."""


@test.skip("pending tryke port")
async def service_group_services_add_remove_entities() -> None:
    """Stub for test_service_group_services_add_remove_entities."""


@test.skip("pending tryke port")
async def service_group_set_group_remove_group() -> None:
    """Stub for test_service_group_set_group_remove_group."""


@test.skip("pending tryke port")
async def group_order() -> None:
    """Stub for test_group_order."""


@test.skip("pending tryke port")
async def group_order_with_dynamic_creation() -> None:
    """Stub for test_group_order_with_dynamic_creation."""


@test.skip("pending tryke port")
async def group_persons() -> None:
    """Stub for test_group_persons."""


@test.skip("pending tryke port")
async def group_persons_and_device_trackers() -> None:
    """Stub for test_group_persons_and_device_trackers."""


@test.skip("pending tryke port")
async def group_mixed_domains_on() -> None:
    """Stub for test_group_mixed_domains_on."""


@test.skip("pending tryke port")
async def group_mixed_domains_off() -> None:
    """Stub for test_group_mixed_domains_off."""


@test.skip("pending tryke port")
async def group_locks() -> None:
    """Stub for test_group_locks."""


@test.skip("pending tryke port")
async def group_sensors() -> None:
    """Stub for test_group_sensors."""


@test.skip("pending tryke port")
async def group_climate_mixed() -> None:
    """Stub for test_group_climate_mixed."""


@test.skip("pending tryke port")
async def group_climate_all_cool() -> None:
    """Stub for test_group_climate_all_cool."""


@test.skip("pending tryke port")
async def group_climate_all_off() -> None:
    """Stub for test_group_climate_all_off."""


@test.skip("pending tryke port")
async def group_alarm() -> None:
    """Stub for test_group_alarm."""


@test.skip("pending tryke port")
async def group_alarm_disarmed() -> None:
    """Stub for test_group_alarm_disarmed."""


@test.skip("pending tryke port")
async def group_vacuum_off() -> None:
    """Stub for test_group_vacuum_off."""


@test.skip("pending tryke port")
async def group_vacuum_on() -> None:
    """Stub for test_group_vacuum_on."""


@test.skip("pending tryke port")
async def device_tracker_or_person_not_home() -> None:
    """Stub for test_device_tracker_or_person_not_home."""


@test.skip("pending tryke port")
async def light_removed() -> None:
    """Stub for test_light_removed."""


@test.skip("pending tryke port")
async def switch_removed() -> None:
    """Stub for test_switch_removed."""


@test.skip("pending tryke port")
async def lights_added_after_group() -> None:
    """Stub for test_lights_added_after_group."""


@test.skip("pending tryke port")
async def lights_added_before_group() -> None:
    """Stub for test_lights_added_before_group."""


@test.skip("pending tryke port")
async def cover_added_after_group() -> None:
    """Stub for test_cover_added_after_group."""


@test.skip("pending tryke port")
async def group_that_references_a_group_of_lights() -> None:
    """Stub for test_group_that_references_a_group_of_lights."""


@test.skip("pending tryke port")
async def group_that_references_a_group_of_covers() -> None:
    """Stub for test_group_that_references_a_group_of_covers."""


@test.skip("pending tryke port")
async def group_that_references_two_groups_of_covers() -> None:
    """Stub for test_group_that_references_two_groups_of_covers."""


@test.skip("pending tryke port")
async def group_that_references_two_types_of_groups() -> None:
    """Stub for test_group_that_references_two_types_of_groups."""


@test.skip("pending tryke port")
async def plant_group() -> None:
    """Stub for test_plant_group."""


@test.skip("pending tryke port")
async def setup_and_remove_config_entry() -> None:
    """Stub for test_setup_and_remove_config_entry."""


@test.skip("pending tryke port")
async def unhide_members_on_remove() -> None:
    """Stub for test_unhide_members_on_remove."""


@test.skip("pending tryke port")
async def entity_platforms_with_multiple_on_states_no_state_match() -> None:
    """Stub for test_entity_platforms_with_multiple_on_states_no_state_match."""


@test.skip("pending tryke port")
async def entity_platforms_with_multiple_on_states_with_state_match() -> None:
    """Stub for test_entity_platforms_with_multiple_on_states_with_state_match."""
