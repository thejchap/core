"""The tests for the Monoprice Blackbird media player platform."""

from collections import defaultdict
from unittest import mock

from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant.components.blackbird.const import DOMAIN, SERVICE_SETALLZONES
from homeassistant.components.blackbird.media_player import (
    DATA_BLACKBIRD,
    PLATFORM_SCHEMA,
)
from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
)
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockEntityPlatform
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


class AttrDict(dict):
    """Helper class for mocking attributes."""

    def __setattr__(self, name, value):
        """Set attribute."""
        self[name] = value

    def __getattr__(self, item):
        """Get attribute."""
        return self[item]


class MockBlackbird:
    """Mock for pyblackbird object."""

    def __init__(self) -> None:
        """Init mock object."""
        self.zones = defaultdict(lambda: AttrDict(power=True, av=1))

    def zone_status(self, zone_id):
        """Get zone status."""
        status = self.zones[zone_id]
        status.zone = zone_id
        return AttrDict(status)

    def set_zone_source(self, zone_id, source_idx):
        """Set source for zone."""
        self.zones[zone_id].av = source_idx

    def set_zone_power(self, zone_id, power):
        """Turn zone on/off."""
        self.zones[zone_id].power = power

    def set_all_zone_source(self, source_idx):
        """Set source for all zones."""
        self.zones[3].av = source_idx


@test
def valid_serial_schema() -> None:
    """Test valid schema."""
    valid_schema = {
        "platform": "blackbird",
        "port": "/dev/ttyUSB0",
        "zones": {
            1: {"name": "a"},
            2: {"name": "a"},
            3: {"name": "a"},
            4: {"name": "a"},
            5: {"name": "a"},
            6: {"name": "a"},
            7: {"name": "a"},
            8: {"name": "a"},
        },
        "sources": {
            1: {"name": "a"},
            2: {"name": "a"},
            3: {"name": "a"},
            4: {"name": "a"},
            5: {"name": "a"},
            6: {"name": "a"},
            7: {"name": "a"},
            8: {"name": "a"},
        },
    }
    PLATFORM_SCHEMA(valid_schema)


@test
def valid_socket_schema() -> None:
    """Test valid schema."""
    valid_schema = {
        "platform": "blackbird",
        "host": "192.168.1.50",
        "zones": {
            1: {"name": "a"},
            2: {"name": "a"},
            3: {"name": "a"},
            4: {"name": "a"},
            5: {"name": "a"},
        },
        "sources": {
            1: {"name": "a"},
            2: {"name": "a"},
            3: {"name": "a"},
            4: {"name": "a"},
        },
    }
    PLATFORM_SCHEMA(valid_schema)


@test
def invalid_schemas() -> None:
    """Test invalid schemas."""
    schemas = (
        {},  # Empty
        None,  # None
        # Port and host used concurrently
        {
            "platform": "blackbird",
            "port": "/dev/ttyUSB0",
            "host": "192.168.1.50",
            "name": "Name",
            "zones": {1: {"name": "a"}},
            "sources": {1: {"name": "b"}},
        },
        # Port or host missing
        {
            "platform": "blackbird",
            "name": "Name",
            "zones": {1: {"name": "a"}},
            "sources": {1: {"name": "b"}},
        },
        # Invalid zone number
        {
            "platform": "blackbird",
            "port": "/dev/ttyUSB0",
            "name": "Name",
            "zones": {11: {"name": "a"}},
            "sources": {1: {"name": "b"}},
        },
        # Invalid source number
        {
            "platform": "blackbird",
            "port": "/dev/ttyUSB0",
            "name": "Name",
            "zones": {1: {"name": "a"}},
            "sources": {9: {"name": "b"}},
        },
        # Zone missing name
        {
            "platform": "blackbird",
            "port": "/dev/ttyUSB0",
            "name": "Name",
            "zones": {1: {}},
            "sources": {1: {"name": "b"}},
        },
        # Source missing name
        {
            "platform": "blackbird",
            "port": "/dev/ttyUSB0",
            "name": "Name",
            "zones": {1: {"name": "a"}},
            "sources": {1: {}},
        },
    )
    for value in schemas:
        expect(lambda v=value: PLATFORM_SCHEMA(v)).to_raise(vol.MultipleInvalid)


@fixture
def mock_blackbird() -> MockBlackbird:
    """Return a mock blackbird instance."""
    return MockBlackbird()


@fixture
async def setup_blackbird(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_blackbird: MockBlackbird = Depends(mock_blackbird),
) -> None:
    """Set up blackbird."""
    with mock.patch(
        "homeassistant.components.blackbird.media_player.get_blackbird",
        return_value=mock_blackbird,
    ):
        await async_setup_component(
            hass,
            "media_player",
            {
                "media_player": {
                    "platform": "blackbird",
                    "port": "/dev/ttyUSB0",
                    "zones": {3: {"name": "Zone name"}},
                    "sources": {
                        1: {"name": "one"},
                        3: {"name": "three"},
                        2: {"name": "two"},
                    },
                }
            },
        )
        await hass.async_block_till_done()


@fixture
def media_player_entity(
    hass: HomeAssistant = Depends(hass_fixture),
    setup_blackbird: None = Depends(setup_blackbird),
) -> MediaPlayerEntity:
    """Return the media player entity."""
    media_player = hass.data[DATA_BLACKBIRD]["/dev/ttyUSB0-3"]
    media_player.hass = hass
    media_player.platform = MockEntityPlatform(hass)
    media_player.entity_id = "media_player.zone_3"
    return media_player


@test
async def setup_platform(
    hass: HomeAssistant = Depends(hass_fixture),
    setup_blackbird: None = Depends(setup_blackbird),
) -> None:
    """Test setting up platform."""
    # One service must be registered
    expect(hass.services.has_service(DOMAIN, SERVICE_SETALLZONES)).to_be(True)
    expect(len(hass.data[DATA_BLACKBIRD])).to_equal(1)
    expect(hass.data[DATA_BLACKBIRD]["/dev/ttyUSB0-3"].name).to_equal("Zone name")


@test
async def setallzones_service_call_with_entity_id(
    hass: HomeAssistant = Depends(hass_fixture),
    media_player_entity: MediaPlayerEntity = Depends(media_player_entity),
    mock_blackbird: MockBlackbird = Depends(mock_blackbird),
) -> None:
    """Test set all zone source service call with entity id."""
    await hass.async_add_executor_job(media_player_entity.update)
    expect(media_player_entity.name).to_equal("Zone name")
    expect(media_player_entity.state).to_equal(STATE_ON)
    expect(media_player_entity.source).to_equal("one")

    # Call set all zones service
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SETALLZONES,
        {"entity_id": "media_player.zone_3", "source": "three"},
        blocking=True,
    )

    # Check that source was changed
    expect(mock_blackbird.zones[3].av).to_equal(3)
    await hass.async_add_executor_job(media_player_entity.update)
    expect(media_player_entity.source).to_equal("three")


@test
async def setallzones_service_call_without_entity_id(
    mock_blackbird: MockBlackbird = Depends(mock_blackbird),
    hass: HomeAssistant = Depends(hass_fixture),
    media_player_entity: MediaPlayerEntity = Depends(media_player_entity),
) -> None:
    """Test set all zone source service call without entity id."""
    await hass.async_add_executor_job(media_player_entity.update)
    expect(media_player_entity.name).to_equal("Zone name")
    expect(media_player_entity.state).to_equal(STATE_ON)
    expect(media_player_entity.source).to_equal("one")

    # Call set all zones service
    await hass.services.async_call(
        DOMAIN, SERVICE_SETALLZONES, {"source": "three"}, blocking=True
    )

    # Check that source was changed
    expect(mock_blackbird.zones[3].av).to_equal(3)
    await hass.async_add_executor_job(media_player_entity.update)
    expect(media_player_entity.source).to_equal("three")


@test
async def update(
    hass: HomeAssistant = Depends(hass_fixture),
    media_player_entity: MediaPlayerEntity = Depends(media_player_entity),
) -> None:
    """Test updating values from blackbird."""
    expect(media_player_entity.state).to_equal(STATE_ON)
    expect(media_player_entity.source).to_equal("one")


@test
async def name(
    media_player_entity: MediaPlayerEntity = Depends(media_player_entity),
) -> None:
    """Test name property."""
    expect(media_player_entity.name).to_equal("Zone name")


@test
async def state(
    hass: HomeAssistant = Depends(hass_fixture),
    media_player_entity: MediaPlayerEntity = Depends(media_player_entity),
    mock_blackbird: MockBlackbird = Depends(mock_blackbird),
) -> None:
    """Test state property."""
    expect(media_player_entity.state).to_equal(STATE_ON)

    mock_blackbird.zones[3].power = False
    await hass.async_add_executor_job(media_player_entity.update)
    expect(media_player_entity.state).to_equal(STATE_OFF)


@test
async def supported_features(
    media_player_entity: MediaPlayerEntity = Depends(media_player_entity),
) -> None:
    """Test supported features property."""
    expect(media_player_entity.supported_features).to_equal(
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )


@test
async def source(
    hass: HomeAssistant = Depends(hass_fixture),
    media_player_entity: MediaPlayerEntity = Depends(media_player_entity),
) -> None:
    """Test source property."""
    expect(media_player_entity.source).to_equal("one")


@test
async def media_title(
    hass: HomeAssistant = Depends(hass_fixture),
    media_player_entity: MediaPlayerEntity = Depends(media_player_entity),
) -> None:
    """Test media title property."""
    expect(media_player_entity.media_title).to_equal("one")


@test
async def source_list(
    media_player_entity: MediaPlayerEntity = Depends(media_player_entity),
) -> None:
    """Test source list property."""
    # Note, the list is sorted!
    expect(media_player_entity.source_list).to_equal(["one", "two", "three"])


@test
async def select_source(
    hass: HomeAssistant = Depends(hass_fixture),
    media_player_entity: MediaPlayerEntity = Depends(media_player_entity),
    mock_blackbird: MockBlackbird = Depends(mock_blackbird),
) -> None:
    """Test source selection methods."""
    await hass.async_add_executor_job(media_player_entity.update)

    expect(media_player_entity.source).to_equal("one")

    await media_player_entity.async_select_source("two")
    expect(mock_blackbird.zones[3].av).to_equal(2)
    await hass.async_add_executor_job(media_player_entity.update)
    expect(media_player_entity.source).to_equal("two")

    # Trying to set unknown source.
    await media_player_entity.async_select_source("no name")
    expect(mock_blackbird.zones[3].av).to_equal(2)
    await hass.async_add_executor_job(media_player_entity.update)
    expect(media_player_entity.source).to_equal("two")


@test
async def turn_on(
    hass: HomeAssistant = Depends(hass_fixture),
    media_player_entity: MediaPlayerEntity = Depends(media_player_entity),
    mock_blackbird: MockBlackbird = Depends(mock_blackbird),
) -> None:
    """Testing turning on the zone."""
    mock_blackbird.zones[3].power = False
    await hass.async_add_executor_job(media_player_entity.update)
    expect(media_player_entity.state).to_equal(STATE_OFF)

    await media_player_entity.async_turn_on()
    expect(mock_blackbird.zones[3].power).to_be(True)
    await hass.async_add_executor_job(media_player_entity.update)
    expect(media_player_entity.state).to_equal(STATE_ON)


@test
async def turn_off(
    hass: HomeAssistant = Depends(hass_fixture),
    media_player_entity: MediaPlayerEntity = Depends(media_player_entity),
    mock_blackbird: MockBlackbird = Depends(mock_blackbird),
) -> None:
    """Testing turning off the zone."""
    mock_blackbird.zones[3].power = True
    await hass.async_add_executor_job(media_player_entity.update)
    expect(media_player_entity.state).to_equal(STATE_ON)

    await media_player_entity.async_turn_off()
    expect(mock_blackbird.zones[3].power).to_be(False)
    await hass.async_add_executor_job(media_player_entity.update)
    expect(media_player_entity.state).to_equal(STATE_OFF)
