"""Test zone component."""

from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import setup
from homeassistant.components import zone
from homeassistant.components.zone import DOMAIN
from homeassistant.const import (
    ATTR_EDITABLE,
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    ATTR_NAME,
    ATTR_PERSONS,
    SERVICE_RELOAD,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import Unauthorized
from homeassistant.helpers import entity_registry as er

from ._fixtures import storage_setup as storage_setup_fx

from tests.common import MockConfigEntry, MockUser
from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fx,
    hass_read_only_user as hass_read_only_user_fx,
    hass_ws_client as hass_ws_client_fx,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.typing import WebSocketGenerator


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-level anchor fixture."""
    return 0


@test
async def setup_no_zones_still_adds_home_zone(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if no config is passed in we still get the home zone."""
    expect(
        await setup.async_setup_component(hass, zone.DOMAIN, {"zone": None})
    ).to_be_truthy()
    expect(len(hass.states.async_entity_ids("zone"))).to_equal(1)
    state = hass.states.get("zone.home")
    expect(hass.config.location_name).to_equal(state.name)
    expect(hass.config.latitude).to_equal(state.attributes["latitude"])
    expect(hass.config.longitude).to_equal(state.attributes["longitude"])
    expect(state.attributes.get("passive", False)).to_be_falsy()


@test
async def setup_test(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a successful setup."""
    info = {
        "name": "Test Zone",
        "latitude": 32.880837,
        "longitude": -117.237561,
        "radius": 250,
        "passive": True,
    }
    expect(
        await setup.async_setup_component(hass, zone.DOMAIN, {"zone": info})
    ).to_be_truthy()

    expect(len(hass.states.async_entity_ids("zone"))).to_equal(2)
    state = hass.states.get("zone.test_zone")
    expect(info["name"]).to_equal(state.name)
    expect(info["latitude"]).to_equal(state.attributes["latitude"])
    expect(info["longitude"]).to_equal(state.attributes["longitude"])
    expect(info["radius"]).to_equal(state.attributes["radius"])
    expect(info["passive"]).to_equal(state.attributes["passive"])


@test
async def setup_zone_skips_home_zone(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that zone named Home should override hass home zone."""
    info = {"name": "Home", "latitude": 1.1, "longitude": -2.2}
    expect(
        await setup.async_setup_component(hass, zone.DOMAIN, {"zone": info})
    ).to_be_truthy()

    expect(len(hass.states.async_entity_ids("zone"))).to_equal(1)
    state = hass.states.get("zone.home")
    expect(info["name"]).to_equal(state.name)


@test
async def setup_name_can_be_same_on_multiple_zones(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that zone named Home should override hass home zone."""
    info = {"name": "Test Zone", "latitude": 1.1, "longitude": -2.2}
    expect(
        await setup.async_setup_component(hass, zone.DOMAIN, {"zone": [info, info]})
    ).to_be_truthy()
    expect(len(hass.states.async_entity_ids("zone"))).to_equal(3)


@test
async def active_zone_skips_passive_zones(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test active and passive zones."""
    expect(
        await setup.async_setup_component(
            hass,
            zone.DOMAIN,
            {
                "zone": [
                    {
                        "name": "Passive Zone",
                        "latitude": 32.880600,
                        "longitude": -117.237561,
                        "radius": 250,
                        "passive": True,
                    }
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    active_zone = zone.async_active_zone(hass, 32.880600, -117.237561)
    expect(active_zone).to_be_none()
    active_zone, in_zones = zone.async_in_zones(hass, 32.880600, -117.237561)
    expect(active_zone).to_be_none()
    expect(in_zones).to_equal(["zone.passive_zone"])


@test
async def active_zone_skips_passive_zones_2(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test active and passive zones."""
    expect(
        await setup.async_setup_component(
            hass,
            zone.DOMAIN,
            {
                "zone": [
                    {
                        "name": "Active Zone",
                        "latitude": 32.880800,
                        "longitude": -117.237561,
                        "radius": 500,
                    }
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    active_zone = zone.async_active_zone(hass, 32.880700, -117.237561)
    expect(active_zone.entity_id).to_equal("zone.active_zone")
    active_zone, in_zones = zone.async_in_zones(hass, 32.880600, -117.237561)
    expect(active_zone.entity_id).to_equal("zone.active_zone")
    expect(in_zones).to_equal(["zone.active_zone"])


@test
async def active_zone_prefers_smaller_zone_if_same_distance(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zone size preferences."""
    latitude = 32.880600
    longitude = -117.237561
    expect(
        await setup.async_setup_component(
            hass,
            zone.DOMAIN,
            {
                "zone": [
                    {
                        "name": "Small Zone",
                        "latitude": latitude,
                        "longitude": longitude,
                        "radius": 250,
                    },
                    {
                        "name": "Big Zone",
                        "latitude": latitude,
                        "longitude": longitude,
                        "radius": 500,
                    },
                ]
            },
        )
    ).to_be_truthy()

    active_zone = zone.async_active_zone(hass, latitude, longitude)
    expect(active_zone.entity_id).to_equal("zone.small_zone")
    active_zone, in_zones = zone.async_in_zones(hass, latitude, longitude)
    expect(active_zone.entity_id).to_equal("zone.small_zone")
    expect(in_zones).to_equal(["zone.small_zone", "zone.big_zone"])


@test
async def active_zone_prefers_smaller_zone_if_same_distance_2(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zone size preferences."""
    latitude = 32.880600
    longitude = -117.237561
    expect(
        await setup.async_setup_component(
            hass,
            zone.DOMAIN,
            {
                "zone": [
                    {
                        "name": "Smallest Zone",
                        "latitude": latitude,
                        "longitude": longitude,
                        "radius": 50,
                    }
                ]
            },
        )
    ).to_be_truthy()

    active_zone = zone.async_active_zone(hass, latitude, longitude)
    expect(active_zone.entity_id).to_equal("zone.smallest_zone")
    active_zone, in_zones = zone.async_in_zones(hass, latitude, longitude)
    expect(active_zone.entity_id).to_equal("zone.smallest_zone")
    expect(in_zones).to_equal(["zone.smallest_zone"])


@test
async def in_zone_works_for_passive_zones(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test working in passive zones."""
    latitude = 32.880600
    longitude = -117.237561
    expect(
        await setup.async_setup_component(
            hass,
            zone.DOMAIN,
            {
                "zone": [
                    {
                        "name": "Passive Zone",
                        "latitude": latitude,
                        "longitude": longitude,
                        "radius": 250,
                        "passive": True,
                    }
                ]
            },
        )
    ).to_be_truthy()

    expect(
        zone.in_zone(hass.states.get("zone.passive_zone"), latitude, longitude)
    ).to_be_truthy()


@test
async def async_active_zone_with_non_zero_radius(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test async_active_zone with a non-zero radius."""
    latitude = 32.880600
    longitude = -117.237561

    expect(
        await setup.async_setup_component(
            hass,
            zone.DOMAIN,
            {
                "zone": [
                    {
                        "name": "Small Zone",
                        "latitude": 32.980600,
                        "longitude": -117.137561,
                        "radius": 50000,
                    },
                    {
                        "name": "Big Zone",
                        "latitude": 32.980600,
                        "longitude": -117.137561,
                        "radius": 100000,
                    },
                ]
            },
        )
    ).to_be_truthy()

    home_state = hass.states.get("zone.home")
    expect(home_state.attributes["radius"]).to_equal(100)
    expect(home_state.attributes["latitude"]).to_equal(32.87336)
    expect(home_state.attributes["longitude"]).to_equal(-117.22743)

    active_zone = zone.async_active_zone(hass, latitude, longitude, 5000)
    expect(active_zone.entity_id).to_equal("zone.home")
    active_zone, in_zones = zone.async_in_zones(hass, latitude, longitude, 5000)
    expect(active_zone.entity_id).to_equal("zone.home")
    expect(in_zones).to_equal(["zone.home", "zone.small_zone", "zone.big_zone"])

    active_zone = zone.async_active_zone(hass, latitude, longitude, 0)
    expect(active_zone.entity_id).to_equal("zone.small_zone")
    active_zone, in_zones = zone.async_in_zones(hass, latitude, longitude, 0)
    expect(active_zone.entity_id).to_equal("zone.small_zone")
    expect(in_zones).to_equal(["zone.small_zone", "zone.big_zone"])


@test
async def core_config_update(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test updating core config will update home zone."""
    expect(await setup.async_setup_component(hass, "zone", {})).to_be_truthy()

    home = hass.states.get("zone.home")

    await hass.config.async_update(
        location_name="Updated Name", latitude=10, longitude=20
    )
    await hass.async_block_till_done()

    home_updated = hass.states.get("zone.home")

    expect(home).not_.to_be(home_updated)
    expect(home_updated.name).to_equal("Updated Name")
    expect(home_updated.attributes["latitude"]).to_equal(10)
    expect(home_updated.attributes["longitude"]).to_equal(20)


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
        await setup.async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: [
                    {"name": "yaml 1", "latitude": 1, "longitude": 2},
                    {"name": "yaml 2", "latitude": 3, "longitude": 4},
                ],
            },
        )
    ).to_be_truthy()

    expect(count_start + 3).to_equal(len(hass.states.async_entity_ids()))

    state_1 = hass.states.get("zone.yaml_1")
    state_2 = hass.states.get("zone.yaml_2")
    state_3 = hass.states.get("zone.yaml_3")

    expect(state_1).not_.to_be_none()
    expect(state_1.attributes["latitude"]).to_equal(1)
    expect(state_1.attributes["longitude"]).to_equal(2)
    expect(state_2).not_.to_be_none()
    expect(state_2.attributes["latitude"]).to_equal(3)
    expect(state_2.attributes["longitude"]).to_equal(4)
    expect(state_3).to_be_none()
    expect(len(entity_registry.entities)).to_equal(0)

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: [
                {"name": "yaml 2", "latitude": 3, "longitude": 4},
                {"name": "yaml 3", "latitude": 5, "longitude": 6},
            ]
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

    expect(count_start + 3).to_equal(len(hass.states.async_entity_ids()))

    state_1 = hass.states.get("zone.yaml_1")
    state_2 = hass.states.get("zone.yaml_2")
    state_3 = hass.states.get("zone.yaml_3")

    expect(state_1).to_be_none()
    expect(state_2).not_.to_be_none()
    expect(state_2.attributes["latitude"]).to_equal(3)
    expect(state_2.attributes["longitude"]).to_equal(4)
    expect(state_3).not_.to_be_none()
    expect(state_3.attributes["latitude"]).to_equal(5)
    expect(state_3.attributes["longitude"]).to_equal(6)


@test
async def load_from_storage(
    hass: HomeAssistant = Depends(hass_fixture),
    storage_setup: Any = Depends(storage_setup_fx),
) -> None:
    """Test set up from storage."""
    expect(await storage_setup()).to_be_truthy()
    state = hass.states.get(f"{DOMAIN}.from_storage")
    expect(state.state).to_equal("0")
    expect(state.name).to_equal("from storage")
    expect(state.attributes.get(ATTR_EDITABLE)).to_be_truthy()


@test
async def editable_state_attribute(
    hass: HomeAssistant = Depends(hass_fixture),
    storage_setup: Any = Depends(storage_setup_fx),
) -> None:
    """Test editable attribute."""
    expect(
        await storage_setup(
            config={DOMAIN: [{"name": "yaml option", "latitude": 3, "longitude": 4}]}
        )
    ).to_be_truthy()

    state = hass.states.get(f"{DOMAIN}.from_storage")
    expect(state.state).to_equal("0")
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("from storage")
    expect(state.attributes.get(ATTR_EDITABLE)).to_be_truthy()

    state = hass.states.get(f"{DOMAIN}.yaml_option")
    expect(state.state).to_equal("0")
    expect(state.attributes.get(ATTR_EDITABLE)).to_be_falsy()


@test
async def ws_list(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Any = Depends(storage_setup_fx),
) -> None:
    """Test listing via WS."""
    expect(
        await storage_setup(
            config={DOMAIN: [{"name": "yaml option", "latitude": 3, "longitude": 4}]}
        )
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
    expect(result[storage_ent][ATTR_NAME]).to_equal("from storage")


@test
async def ws_delete(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    storage_setup: Any = Depends(storage_setup_fx),
) -> None:
    """Test WS delete cleans up entity registry."""
    expect(await storage_setup()).to_be_truthy()

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    expect(state).not_.to_be_none()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id)
    ).not_.to_be_none()

    client = await hass_ws_client(hass)

    await client.send_json(
        {"id": 6, "type": f"{DOMAIN}/delete", f"{DOMAIN}_id": f"{input_id}"}
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be_truthy()

    state = hass.states.get(input_entity_id)
    expect(state).to_be_none()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id)
    ).to_be_none()


@test
async def update(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    storage_setup: Any = Depends(storage_setup_fx),
) -> None:
    """Test updating min/max updates the state."""

    items = [
        {
            "id": "from_storage",
            "name": "from storage",
            "latitude": 1,
            "longitude": 2,
            "radius": 3,
            "passive": False,
        }
    ]
    expect(await storage_setup(items)).to_be_truthy()

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    expect(state.attributes["latitude"]).to_equal(1)
    expect(state.attributes["longitude"]).to_equal(2)
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id)
    ).not_.to_be_none()

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": f"{input_id}",
            "latitude": 3,
            "longitude": 4,
            "passive": True,
        }
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be_truthy()

    state = hass.states.get(input_entity_id)
    expect(state.attributes["latitude"]).to_equal(3)
    expect(state.attributes["longitude"]).to_equal(4)
    expect(state.attributes["passive"]).to_be(True)


@test
async def ws_create(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    storage_setup: Any = Depends(storage_setup_fx),
) -> None:
    """Test create WS."""
    expect(await storage_setup(items=[])).to_be_truthy()

    input_id = "new_input"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    expect(state).to_be_none()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id)
    ).to_be_none()

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/create",
            "name": "New Input",
            "latitude": 3,
            "longitude": 4,
            "passive": True,
        }
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be_truthy()

    state = hass.states.get(input_entity_id)
    expect(state.state).to_equal("0")
    expect(state.attributes["latitude"]).to_equal(3)
    expect(state.attributes["longitude"]).to_equal(4)
    expect(state.attributes["passive"]).to_be(True)


@test
async def import_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we import config entry and then delete it."""
    entry = MockConfigEntry(
        domain="zone",
        data={
            "name": "from config entry",
            "latitude": 1,
            "longitude": 2,
            "radius": 3,
            "passive": False,
            "icon": "mdi:from-config-entry",
        },
    )
    entry.add_to_hass(hass)
    expect(await setup.async_setup_component(hass, DOMAIN, {})).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.config_entries.async_entries())).to_equal(0)

    state = hass.states.get("zone.from_config_entry")
    expect(state).not_.to_be_none()
    expect(state.attributes[zone.ATTR_LATITUDE]).to_equal(1)
    expect(state.attributes[zone.ATTR_LONGITUDE]).to_equal(2)
    expect(state.attributes[zone.ATTR_RADIUS]).to_equal(3)
    expect(state.attributes[zone.ATTR_PASSIVE]).to_be(False)
    expect(state.attributes[ATTR_ICON]).to_equal("mdi:from-config-entry")


@test
async def zone_empty_setup(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up zone with empty config."""
    expect(
        await setup.async_setup_component(hass, DOMAIN, {"zone": {}})
    ).to_be_truthy()


@test
async def unavailable_zone(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test active zone with unavailable zones."""
    expect(
        await setup.async_setup_component(hass, DOMAIN, {"zone": {}})
    ).to_be_truthy()
    hass.states.async_set("zone.bla", "unavailable", {"restored": True})

    expect(zone.async_active_zone(hass, 0.0, 0.01)).to_be_none()
    active_zone, in_zones = zone.async_in_zones(hass, 0.0, 0.01)
    expect(active_zone).to_be_none()
    expect(in_zones).to_equal([])

    expect(zone.in_zone(hass.states.get("zone.bla"), 0, 0)).to_be(False)


@test
async def state(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the state of a zone."""
    info = {
        "name": "Test Zone",
        "latitude": 32.880837,
        "longitude": -117.237561,
        "radius": 250,
        "passive": False,
    }
    expect(
        await setup.async_setup_component(hass, zone.DOMAIN, {"zone": info})
    ).to_be_truthy()

    expect(len(hass.states.async_entity_ids("zone"))).to_equal(2)
    state = hass.states.get("zone.test_zone")
    expect(state.state).to_equal("0")
    expect(state.attributes[ATTR_PERSONS]).to_equal([])

    # Person entity enters zone
    hass.states.async_set(
        "person.person1",
        "Test Zone",
    )
    await hass.async_block_till_done()

    state = hass.states.get("zone.test_zone")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("1")
    expect(state.attributes[ATTR_PERSONS]).to_equal(["person.person1"])

    state = hass.states.get("zone.home")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("0")
    expect(state.attributes[ATTR_PERSONS]).to_equal([])

    # Person entity enters zone (case insensitive)
    hass.states.async_set(
        "person.person2",
        "TEST zone",
    )
    await hass.async_block_till_done()

    state = hass.states.get("zone.test_zone")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("2")
    expect(sorted(state.attributes[ATTR_PERSONS])).to_equal(
        ["person.person1", "person.person2"]
    )

    state = hass.states.get("zone.home")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("0")
    expect(state.attributes[ATTR_PERSONS]).to_equal([])

    # Person entity enters another zone
    hass.states.async_set(
        "person.person1",
        "home",
    )
    await hass.async_block_till_done()

    state = hass.states.get("zone.test_zone")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("1")
    expect(state.attributes[ATTR_PERSONS]).to_equal(["person.person2"])

    state = hass.states.get("zone.home")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("1")
    expect(state.attributes[ATTR_PERSONS]).to_equal(["person.person1"])

    # Person entity enters not_home
    hass.states.async_set(
        "person.person1",
        "not_home",
    )
    await hass.async_block_till_done()

    state = hass.states.get("zone.test_zone")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("1")
    expect(state.attributes[ATTR_PERSONS]).to_equal(["person.person2"])

    # Person entity removed
    hass.states.async_remove("person.person2")
    await hass.async_block_till_done()

    state = hass.states.get("zone.test_zone")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("0")
    expect(state.attributes[ATTR_PERSONS]).to_equal([])

    state = hass.states.get("zone.home")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("0")
    expect(state.attributes[ATTR_PERSONS]).to_equal([])
