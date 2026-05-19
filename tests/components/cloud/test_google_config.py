"""Test the Cloud Google Config."""

from collections.abc import Generator
from http import HTTPStatus
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

from freezegun import freeze_time
import jwt
from tryke import Depends, expect, fixture, test

from homeassistant.components.cloud import GACTIONS_SCHEMA
from homeassistant.components.cloud.const import (
    DATA_CLOUD,
    PREF_DISABLE_2FA,
    PREF_GOOGLE_DEFAULT_EXPOSE,
    PREF_GOOGLE_ENTITY_CONFIGS,
    PREF_SHOULD_EXPOSE,
)
from homeassistant.components.cloud.google_config import CloudGoogleConfig
from homeassistant.components.cloud.prefs import CloudPreferences
from homeassistant.components.google_assistant import helpers as ga_helpers
from homeassistant.components.homeassistant.exposed_entities import (
    DATA_EXPOSED_ENTITIES,
    async_expose_entity,
    async_get_entity_settings,
)
from homeassistant.const import (
    EVENT_HOMEASSISTANT_START,
    EVENT_HOMEASSISTANT_STARTED,
    EntityCategory,
)
from homeassistant.core import CoreState, HomeAssistant, State
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util.dt import utcnow

from . import mock_cloud
from ._fixtures import load_homeassistant

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _load_homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@fixture
async def cloud_prefs(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> CloudPreferences:
    """Fixture for cloud preferences."""
    prefs = CloudPreferences(hass)
    await prefs.async_initialize()
    return prefs


@fixture
async def mock_conf(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
) -> CloudGoogleConfig:
    """Mock Google conf."""
    return CloudGoogleConfig(
        hass,
        GACTIONS_SCHEMA({}),
        "mock-user-id",
        cloud_prefs_inst,
        Mock(username="abcdefghjkl"),
    )


@fixture
async def mock_cloud_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up the cloud."""
    await mock_cloud(hass)
    await hass.async_block_till_done()


@fixture
def mock_cloud_login(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(mock_cloud_setup),
) -> Generator[None]:
    """Mock cloud is logged in."""
    hass.data[DATA_CLOUD].id_token = jwt.encode(
        {
            "email": "hello@home-assistant.io",
            "custom:sub-exp": "2300-01-03",
            "cognito:username": "abcdefghjkl",
        },
        "test",
    )
    with patch.object(hass.data[DATA_CLOUD].auth, "async_check_token"):
        yield


@fixture
async def mock_cloud_login_prefs(
    _login: None = Depends(mock_cloud_login),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
) -> CloudPreferences:
    """Provide a standalone CloudPreferences after mock_cloud_login is set up."""
    return cloud_prefs_inst


def _set_expired_cloud_login(hass: HomeAssistant) -> None:
    """Mock the cloud as logged in with an expired subscription."""
    hass.data[DATA_CLOUD].id_token = jwt.encode(
        {
            "email": "hello@home-assistant.io",
            "custom:sub-exp": "2018-01-01",
            "cognito:username": "abcdefghjkl",
        },
        "test",
    )


def expose_new(hass: HomeAssistant, expose_new: bool) -> None:
    """Enable exposing new entities to Google."""
    exposed_entities = hass.data[DATA_EXPOSED_ENTITIES]
    exposed_entities.async_set_expose_new_entities("cloud.google_assistant", expose_new)


def expose_entity(hass: HomeAssistant, entity_id: str, should_expose: bool) -> None:
    """Expose an entity to Google."""
    async_expose_entity(hass, "cloud.google_assistant", entity_id, should_expose)


@test
async def google_update_report_state(
    hass: HomeAssistant = Depends(hass_fixture),
    conf: CloudGoogleConfig = Depends(mock_conf),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
) -> None:
    """Test Google config responds to updating preference."""
    await conf.async_initialize()
    await conf.async_connect_agent_user("mock-user-id")

    conf._cloud.subscription_expired = False

    with (
        patch.object(conf, "async_sync_entities") as mock_sync,
        patch(
            "homeassistant.components.google_assistant.report_state.async_enable_report_state"
        ) as mock_report_state,
    ):
        await cloud_prefs_inst.async_update(google_report_state=True)
        await hass.async_block_till_done()

    expect(len(mock_sync.mock_calls)).to_equal(1)
    expect(len(mock_report_state.mock_calls)).to_equal(1)


@test
async def google_update_report_state_subscription_expired(
    hass: HomeAssistant = Depends(hass_fixture),
    conf: CloudGoogleConfig = Depends(mock_conf),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
) -> None:
    """Test Google config not reporting state when subscription has expired."""
    await conf.async_initialize()
    await conf.async_connect_agent_user("mock-user-id")

    expect(bool(conf._cloud.subscription_expired)).to_be(True)

    with (
        patch.object(conf, "async_sync_entities") as mock_sync,
        patch(
            "homeassistant.components.google_assistant.report_state.async_enable_report_state"
        ) as mock_report_state,
    ):
        await cloud_prefs_inst.async_update(google_report_state=True)
        await hass.async_block_till_done()

    expect(len(mock_sync.mock_calls)).to_equal(0)
    expect(len(mock_report_state.mock_calls)).to_equal(0)


@test
async def sync_entities(
    conf: CloudGoogleConfig = Depends(mock_conf),
) -> None:
    """Test sync devices."""
    await conf.async_initialize()
    expect(len(conf.async_get_agent_users())).to_equal(0)

    await conf.async_connect_agent_user("mock-user-id")

    expect(len(conf.async_get_agent_users())).to_equal(1)

    conf._cloud.google_report_state.request_sync = AsyncMock(
        return_value=Mock(status=HTTPStatus.NOT_FOUND)
    )

    expect(await conf.async_sync_entities("mock-user-id")).to_equal(HTTPStatus.NOT_FOUND)
    expect(len(conf.async_get_agent_users())).to_equal(0)
    expect(len(conf._cloud.google_report_state.request_sync.mock_calls)).to_equal(1)


@test
async def google_update_expose_trigger_sync(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
) -> None:
    """Test Google config responds to updating exposed entities."""
    expose_new(hass, True)
    binary_sensor_entry = entity_registry.async_get_or_create(
        "binary_sensor", "test", "unique", suggested_object_id="door"
    )
    sensor_entry = entity_registry.async_get_or_create(
        "sensor", "test", "unique", suggested_object_id="temp"
    )
    light_entry = entity_registry.async_get_or_create(
        "light", "test", "unique", suggested_object_id="kitchen"
    )

    with freeze_time(utcnow()):
        config = CloudGoogleConfig(
            hass,
            GACTIONS_SCHEMA({}),
            "mock-user-id",
            cloud_prefs_inst,
            Mock(username="abcdefghjkl"),
        )
        await config.async_initialize()
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()
        await config.async_connect_agent_user("mock-user-id")

        with (
            patch.object(config, "async_sync_entities") as mock_sync,
            patch.object(ga_helpers, "SYNC_DELAY", 0),
        ):
            expose_entity(hass, light_entry.entity_id, True)
            await hass.async_block_till_done()
            async_fire_time_changed(hass, utcnow())
            await hass.async_block_till_done()

        expect(len(mock_sync.mock_calls)).to_equal(1)

        with (
            patch.object(config, "async_sync_entities") as mock_sync,
            patch.object(ga_helpers, "SYNC_DELAY", 0),
        ):
            expose_entity(hass, light_entry.entity_id, False)
            expose_entity(hass, binary_sensor_entry.entity_id, True)
            expose_entity(hass, sensor_entry.entity_id, True)
            await hass.async_block_till_done()
            async_fire_time_changed(hass, utcnow())
            await hass.async_block_till_done()

        expect(len(mock_sync.mock_calls)).to_equal(1)


@test
async def google_entity_registry_sync(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(mock_cloud_login_prefs),
) -> None:
    """Test Google config responds to entity registry."""
    expose_new(hass, True)

    config = CloudGoogleConfig(
        hass,
        GACTIONS_SCHEMA({}),
        "mock-user-id",
        cloud_prefs_inst,
        hass.data[DATA_CLOUD],
    )
    with (
        patch.object(config, "async_sync_entities_all"),
        patch.object(config, "async_enable_report_state"),
    ):
        await config.async_initialize()
        await config.async_connect_agent_user("mock-user-id")

    with (
        patch.object(config, "async_schedule_google_sync_all") as mock_sync,
        patch.object(config, "async_sync_entities_all"),
        patch.object(ga_helpers, "SYNC_DELAY", 0),
    ):
        entry = entity_registry.async_get_or_create(
            "light", "test", "unique", suggested_object_id="kitchen"
        )
        await hass.async_block_till_done()

        expect(len(mock_sync.mock_calls)).to_equal(1)

        hass.bus.async_fire(
            er.EVENT_ENTITY_REGISTRY_UPDATED,
            {"action": "remove", "entity_id": entry.entity_id},
        )
        await hass.async_block_till_done()

        expect(len(mock_sync.mock_calls)).to_equal(2)

        hass.bus.async_fire(
            er.EVENT_ENTITY_REGISTRY_UPDATED,
            {
                "action": "update",
                "entity_id": entry.entity_id,
                "changes": ["entity_id"],
            },
        )
        await hass.async_block_till_done()

        expect(len(mock_sync.mock_calls)).to_equal(3)

        hass.bus.async_fire(
            er.EVENT_ENTITY_REGISTRY_UPDATED,
            {"action": "update", "entity_id": entry.entity_id, "changes": ["icon"]},
        )
        await hass.async_block_till_done()

        expect(len(mock_sync.mock_calls)).to_equal(3)

        hass.set_state(CoreState.starting)
        hass.bus.async_fire(
            er.EVENT_ENTITY_REGISTRY_UPDATED,
            {"action": "create", "entity_id": entry.entity_id},
        )
        await hass.async_block_till_done()

        expect(len(mock_sync.mock_calls)).to_equal(3)


@test
async def google_device_registry_sync(
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(mock_cloud_login_prefs),
) -> None:
    """Test Google config responds to device registry."""
    config = CloudGoogleConfig(
        hass,
        GACTIONS_SCHEMA({}),
        "mock-user-id",
        cloud_prefs_inst,
        hass.data[DATA_CLOUD],
    )

    expose_new(hass, True)

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry = entity_registry.async_get_or_create(
        "light", "hue", "1234", device_id=device_entry.id
    )
    entity_entry = entity_registry.async_update_entity(
        entity_entry.entity_id, area_id="ABCD"
    )

    with patch.object(config, "async_sync_entities_all"):
        await config.async_initialize()
        await hass.async_block_till_done()
        await config.async_connect_agent_user("mock-user-id")
        await hass.async_block_till_done()

    with patch.object(config, "async_schedule_google_sync_all") as mock_sync:
        hass.bus.async_fire(
            dr.EVENT_DEVICE_REGISTRY_UPDATED,
            {
                "action": "update",
                "device_id": device_entry.id,
                "changes": ["manufacturer"],
            },
        )
        await hass.async_block_till_done()

        expect(len(mock_sync.mock_calls)).to_equal(0)

        hass.bus.async_fire(
            dr.EVENT_DEVICE_REGISTRY_UPDATED,
            {
                "action": "update",
                "device_id": device_entry.id,
                "changes": ["area_id"],
            },
        )
        await hass.async_block_till_done()

        expect(len(mock_sync.mock_calls)).to_equal(0)

        entity_registry.async_update_entity(entity_entry.entity_id, area_id=None)

        hass.bus.async_fire(
            dr.EVENT_DEVICE_REGISTRY_UPDATED,
            {
                "action": "update",
                "device_id": device_entry.id,
                "changes": ["area_id"],
            },
        )
        await hass.async_block_till_done()

        expect(len(mock_sync.mock_calls)).to_equal(1)


@test
async def sync_google_when_started(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(mock_cloud_login_prefs),
) -> None:
    """Test Google config syncs on init."""
    config = CloudGoogleConfig(
        hass,
        GACTIONS_SCHEMA({}),
        "mock-user-id",
        cloud_prefs_inst,
        hass.data[DATA_CLOUD],
    )
    with patch.object(config, "async_sync_entities_all") as mock_sync:
        await config.async_initialize()
        await hass.async_block_till_done()
        expect(len(mock_sync.mock_calls)).to_equal(1)


@test
async def sync_google_on_home_assistant_start(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(mock_cloud_login_prefs),
) -> None:
    """Test Google config syncs when home assistant started."""
    config = CloudGoogleConfig(
        hass,
        GACTIONS_SCHEMA({}),
        "mock-user-id",
        cloud_prefs_inst,
        hass.data[DATA_CLOUD],
    )
    hass.set_state(CoreState.not_running)
    with patch.object(config, "async_sync_entities_all") as mock_sync:
        await config.async_initialize()
        await hass.async_block_till_done()
        expect(len(mock_sync.mock_calls)).to_equal(0)

        hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
        await hass.async_block_till_done()
        expect(len(mock_sync.mock_calls)).to_equal(1)


@test
async def google_config_expose_entity_prefs(
    hass: HomeAssistant = Depends(hass_fixture),
    conf: CloudGoogleConfig = Depends(mock_conf),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test Google config should expose using prefs."""
    entity_entry1 = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_config_id",
        suggested_object_id="config_light",
        entity_category=EntityCategory.CONFIG,
    )
    entity_entry2 = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_diagnostic_id",
        suggested_object_id="diagnostic_light",
        entity_category=EntityCategory.DIAGNOSTIC,
    )
    entity_entry3 = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_hidden_integration_id",
        suggested_object_id="hidden_integration_light",
        hidden_by=er.RegistryEntryHider.INTEGRATION,
    )
    entity_entry4 = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_hidden_user_id",
        suggested_object_id="hidden_user_light",
        hidden_by=er.RegistryEntryHider.USER,
    )
    entity_entry5 = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_basement_id",
        suggested_object_id="basement",
    )
    entity_entry6 = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_entrance_id",
        suggested_object_id="entrance",
    )

    expose_new(hass, True)
    expose_entity(hass, entity_entry5.entity_id, False)

    state = State("light.kitchen", "on")
    state_config = State(entity_entry1.entity_id, "on")
    state_diagnostic = State(entity_entry2.entity_id, "on")
    state_hidden_integration = State(entity_entry3.entity_id, "on")
    state_hidden_user = State(entity_entry4.entity_id, "on")
    state_not_exposed = State(entity_entry5.entity_id, "on")
    state_exposed_default = State(entity_entry6.entity_id, "on")

    expose_entity(hass, "light.kitchen", True)
    expect(bool(conf.should_expose(state))).to_be(True)
    expect(bool(conf.should_expose(state_config))).to_be(False)
    expect(bool(conf.should_expose(state_diagnostic))).to_be(False)
    expect(bool(conf.should_expose(state_hidden_integration))).to_be(False)
    expect(bool(conf.should_expose(state_hidden_user))).to_be(False)
    expect(bool(conf.should_expose(state_not_exposed))).to_be(False)
    expect(bool(conf.should_expose(state_exposed_default))).to_be(True)

    expose_entity(hass, entity_entry5.entity_id, True)
    expect(bool(conf.should_expose(state_not_exposed))).to_be(True)

    expose_entity(hass, entity_entry5.entity_id, None)
    expect(bool(conf.should_expose(state_not_exposed))).to_be(False)


@test
async def enabled_requires_valid_sub(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(mock_cloud_setup),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
) -> None:
    """Test that google config enabled requires a valid Cloud sub."""
    _set_expired_cloud_login(hass)

    expect(bool(cloud_prefs_inst.google_enabled)).to_be(True)
    expect(bool(hass.data[DATA_CLOUD].is_logged_in)).to_be(True)
    expect(bool(hass.data[DATA_CLOUD].subscription_expired)).to_be(True)

    config = CloudGoogleConfig(
        hass,
        GACTIONS_SCHEMA({}),
        "mock-user-id",
        cloud_prefs_inst,
        hass.data[DATA_CLOUD],
    )

    expect(bool(config.enabled)).to_be(False)


@test
async def setup_google_assistant(
    hass: HomeAssistant = Depends(hass_fixture),
    conf: CloudGoogleConfig = Depends(mock_conf),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
) -> None:
    """Test that we set up the google_assistant integration if enabled in cloud."""
    conf._cloud.subscription_expired = False

    expect("google_assistant" in hass.config.components).to_be(False)

    await conf.async_initialize()
    await hass.async_block_till_done()
    expect("google_assistant" in hass.config.components).to_be(True)

    hass.config.components.remove("google_assistant")

    await cloud_prefs_inst.async_update()
    await hass.async_block_till_done()
    expect("google_assistant" in hass.config.components).to_be(True)


@test
async def google_handle_logout(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(mock_cloud_login_prefs),
) -> None:
    """Test Google config responds to logging out."""
    gconf = CloudGoogleConfig(
        hass,
        GACTIONS_SCHEMA({}),
        "mock-user-id",
        cloud_prefs_inst,
        Mock(is_logged_in=False),
    )

    await gconf.async_initialize()

    with patch(
        "homeassistant.components.google_assistant.report_state.async_enable_report_state",
    ) as mock_enable:
        gconf.async_enable_report_state()
        await hass.async_block_till_done()

    expect(len(mock_enable.mock_calls)).to_equal(1)
    expect(len(gconf._on_deinitialize)).to_equal(6)

    await cloud_prefs_inst.get_cloud_user()

    with patch.object(
        hass.data[DATA_CLOUD].auth,
        "async_check_token",
        side_effect=AssertionError("Should not be called"),
    ):
        await cloud_prefs_inst.async_set_username(None)
        gconf.async_deinitialize()
        await hass.async_block_till_done()
        expect(bool(gconf._on_deinitialize)).to_be(False)

    expect(len(mock_enable.return_value.mock_calls)).to_equal(1)


@test.cases(
    test.case("v1", google_settings_version=1),
    test.case("v2", google_settings_version=2),
)
async def google_config_migrate_expose_entity_prefs(
    google_settings_version: int,
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test migrating Google entity config."""
    hass.set_state(CoreState.not_running)

    hass.states.async_set("light.state_only", "on")
    entity_exposed = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_exposed",
        suggested_object_id="exposed",
    )

    entity_no_2fa_exposed = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_no_2fa_exposed",
        suggested_object_id="no_2fa_exposed",
    )

    entity_migrated = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_migrated",
        suggested_object_id="migrated",
    )

    entity_config = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_config",
        suggested_object_id="config",
        entity_category=EntityCategory.CONFIG,
    )

    entity_default = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_default",
        suggested_object_id="default",
    )

    entity_blocked = entity_registry.async_get_or_create(
        "group",
        "test",
        "group_all_locks",
        suggested_object_id="all_locks",
    )
    expect(entity_blocked.entity_id).to_equal("group.all_locks")

    await cloud_prefs_inst.async_update(
        google_enabled=True,
        google_report_state=False,
        google_settings_version=google_settings_version,
    )
    expose_entity(hass, entity_migrated.entity_id, False)

    cloud_prefs_inst._prefs[PREF_GOOGLE_ENTITY_CONFIGS]["light.unknown"] = {
        PREF_SHOULD_EXPOSE: True,
        PREF_DISABLE_2FA: True,
    }
    cloud_prefs_inst._prefs[PREF_GOOGLE_ENTITY_CONFIGS]["light.state_only"] = {
        PREF_SHOULD_EXPOSE: False
    }
    cloud_prefs_inst._prefs[PREF_GOOGLE_ENTITY_CONFIGS][entity_exposed.entity_id] = {
        PREF_SHOULD_EXPOSE: True
    }
    cloud_prefs_inst._prefs[PREF_GOOGLE_ENTITY_CONFIGS][
        entity_no_2fa_exposed.entity_id
    ] = {
        PREF_SHOULD_EXPOSE: True,
        PREF_DISABLE_2FA: True,
    }
    cloud_prefs_inst._prefs[PREF_GOOGLE_ENTITY_CONFIGS][entity_migrated.entity_id] = {
        PREF_SHOULD_EXPOSE: True
    }
    conf = CloudGoogleConfig(
        hass,
        GACTIONS_SCHEMA({}),
        "mock-user-id",
        cloud_prefs_inst,
        Mock(is_logged_in=False),
    )
    await conf.async_initialize()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    expect(async_get_entity_settings(hass, "light.unknown")).to_equal(
        {"cloud.google_assistant": {"disable_2fa": True, "should_expose": True}}
    )
    expect(async_get_entity_settings(hass, "light.state_only")).to_equal(
        {"cloud.google_assistant": {"should_expose": False}}
    )
    expect(async_get_entity_settings(hass, entity_exposed.entity_id)).to_equal(
        {"cloud.google_assistant": {"should_expose": True}}
    )
    expect(async_get_entity_settings(hass, entity_migrated.entity_id)).to_equal(
        {"cloud.google_assistant": {"should_expose": True}}
    )
    expect(async_get_entity_settings(hass, entity_no_2fa_exposed.entity_id)).to_equal(
        {"cloud.google_assistant": {"disable_2fa": True, "should_expose": True}}
    )
    expect(async_get_entity_settings(hass, entity_config.entity_id)).to_equal(
        {"cloud.google_assistant": {"should_expose": False}}
    )
    expect(async_get_entity_settings(hass, entity_default.entity_id)).to_equal(
        {"cloud.google_assistant": {"should_expose": True}}
    )
    expect(async_get_entity_settings(hass, entity_blocked.entity_id)).to_equal(
        {"cloud.google_assistant": {"should_expose": False}}
    )


@test
async def google_config_migrate_expose_entity_prefs_v2_no_exposed(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test migrating Google entity config from v2 to v3 when no entity is exposed."""
    hass.set_state(CoreState.not_running)

    hass.states.async_set("light.state_only", "on")
    entity_migrated = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_migrated",
        suggested_object_id="migrated",
    )
    await cloud_prefs_inst.async_update(
        google_enabled=True,
        google_report_state=False,
        google_settings_version=2,
    )
    expose_entity(hass, "light.state_only", False)
    expose_entity(hass, entity_migrated.entity_id, False)

    cloud_prefs_inst._prefs[PREF_GOOGLE_ENTITY_CONFIGS]["light.state_only"] = {
        PREF_SHOULD_EXPOSE: True
    }
    cloud_prefs_inst._prefs[PREF_GOOGLE_ENTITY_CONFIGS][entity_migrated.entity_id] = {
        PREF_SHOULD_EXPOSE: True
    }
    conf = CloudGoogleConfig(
        hass,
        GACTIONS_SCHEMA({}),
        "mock-user-id",
        cloud_prefs_inst,
        Mock(is_logged_in=False),
    )
    await conf.async_initialize()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    expect(async_get_entity_settings(hass, "light.state_only")).to_equal(
        {"cloud.google_assistant": {"should_expose": True}}
    )
    expect(async_get_entity_settings(hass, entity_migrated.entity_id)).to_equal(
        {"cloud.google_assistant": {"should_expose": True}}
    )


@test
async def google_config_migrate_expose_entity_prefs_v2_exposed(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test migrating Google entity config from v2 to v3 when an entity is exposed."""
    hass.set_state(CoreState.not_running)

    hass.states.async_set("light.state_only", "on")
    entity_migrated = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_migrated",
        suggested_object_id="migrated",
    )
    await cloud_prefs_inst.async_update(
        google_enabled=True,
        google_report_state=False,
        google_settings_version=2,
    )
    expose_entity(hass, "light.state_only", False)
    expose_entity(hass, entity_migrated.entity_id, True)

    cloud_prefs_inst._prefs[PREF_GOOGLE_ENTITY_CONFIGS]["light.state_only"] = {
        PREF_SHOULD_EXPOSE: True
    }
    cloud_prefs_inst._prefs[PREF_GOOGLE_ENTITY_CONFIGS][entity_migrated.entity_id] = {
        PREF_SHOULD_EXPOSE: True
    }
    conf = CloudGoogleConfig(
        hass,
        GACTIONS_SCHEMA({}),
        "mock-user-id",
        cloud_prefs_inst,
        Mock(is_logged_in=False),
    )
    await conf.async_initialize()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    expect(async_get_entity_settings(hass, "light.state_only")).to_equal(
        {"cloud.google_assistant": {"should_expose": False}}
    )
    expect(async_get_entity_settings(hass, entity_migrated.entity_id)).to_equal(
        {"cloud.google_assistant": {"should_expose": True}}
    )


@test
async def google_config_migrate_expose_entity_prefs_default_none(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test migrating Google entity config."""
    hass.set_state(CoreState.not_running)

    entity_default = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_default",
        suggested_object_id="default",
    )

    await cloud_prefs_inst.async_update(
        google_enabled=True,
        google_report_state=False,
        google_settings_version=1,
    )

    cloud_prefs_inst._prefs[PREF_GOOGLE_DEFAULT_EXPOSE] = None
    conf = CloudGoogleConfig(
        hass,
        GACTIONS_SCHEMA({}),
        "mock-user-id",
        cloud_prefs_inst,
        Mock(is_logged_in=False),
    )
    await conf.async_initialize()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    expect(async_get_entity_settings(hass, entity_default.entity_id)).to_equal(
        {"cloud.google_assistant": {"should_expose": True}}
    )


@test
async def google_config_migrate_expose_entity_prefs_default(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test migrating Google entity config."""
    hass.set_state(CoreState.not_running)

    binary_sensor_supported = entity_registry.async_get_or_create(
        "binary_sensor",
        "test",
        "binary_sensor_supported",
        original_device_class="door",
        suggested_object_id="supported",
    )

    binary_sensor_unsupported = entity_registry.async_get_or_create(
        "binary_sensor",
        "test",
        "binary_sensor_unsupported",
        original_device_class="battery",
        suggested_object_id="unsupported",
    )

    light = entity_registry.async_get_or_create(
        "light",
        "test",
        "unique",
        suggested_object_id="light",
    )

    sensor_supported = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "sensor_supported",
        original_device_class="temperature",
        suggested_object_id="supported",
    )

    sensor_unsupported = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "sensor_unsupported",
        original_device_class="battery",
        suggested_object_id="unsupported",
    )

    water_heater = entity_registry.async_get_or_create(
        "water_heater",
        "test",
        "unique",
        suggested_object_id="water_heater",
    )

    await cloud_prefs_inst.async_update(
        google_enabled=True,
        google_report_state=False,
        google_settings_version=1,
    )

    cloud_prefs_inst._prefs[PREF_GOOGLE_DEFAULT_EXPOSE] = [
        "binary_sensor",
        "light",
        "sensor",
        "water_heater",
    ]
    conf = CloudGoogleConfig(
        hass,
        GACTIONS_SCHEMA({}),
        "mock-user-id",
        cloud_prefs_inst,
        Mock(is_logged_in=False),
    )
    await conf.async_initialize()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    expect(async_get_entity_settings(hass, binary_sensor_supported.entity_id)).to_equal(
        {"cloud.google_assistant": {"should_expose": True}}
    )
    expect(
        async_get_entity_settings(hass, binary_sensor_unsupported.entity_id)
    ).to_equal({"cloud.google_assistant": {"should_expose": False}})
    expect(async_get_entity_settings(hass, light.entity_id)).to_equal(
        {"cloud.google_assistant": {"should_expose": True}}
    )
    expect(async_get_entity_settings(hass, sensor_supported.entity_id)).to_equal(
        {"cloud.google_assistant": {"should_expose": True}}
    )
    expect(async_get_entity_settings(hass, sensor_unsupported.entity_id)).to_equal(
        {"cloud.google_assistant": {"should_expose": False}}
    )
    expect(async_get_entity_settings(hass, water_heater.entity_id)).to_equal(
        {"cloud.google_assistant": {"should_expose": False}}
    )


@test
async def google_config_get_agent_user_id(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(mock_cloud_login_prefs),
) -> None:
    """Test overridden get_agent_user_id_from_webhook method."""
    config = CloudGoogleConfig(
        hass,
        GACTIONS_SCHEMA({}),
        "mock-user-id",
        cloud_prefs_inst,
        hass.data[DATA_CLOUD],
    )
    expect(
        config.get_agent_user_id_from_webhook(cloud_prefs_inst.google_local_webhook_id)
        == config.agent_user_id
    ).to_be(True)
    expect(
        config.get_agent_user_id_from_webhook("other_id") != config.agent_user_id
    ).to_be(True)


@test
async def google_config_get_agent_users(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(mock_cloud_login_prefs),
) -> None:
    """Test overridden async_get_agent_users method."""
    username_mock = PropertyMock(return_value="blah")

    cloud_prefs_inst._prefs["google_connected"] = True
    expect(bool(cloud_prefs_inst.google_connected)).to_be(True)
    mock_cloud_obj = Mock(is_logged_in=False)
    type(mock_cloud_obj).username = username_mock
    config = CloudGoogleConfig(
        hass, GACTIONS_SCHEMA({}), "mock-user-id", cloud_prefs_inst, mock_cloud_obj
    )
    expect(config.async_get_agent_users()).to_equal(())
    username_mock.assert_not_called()

    cloud_prefs_inst._prefs["google_connected"] = False
    expect(bool(cloud_prefs_inst.google_connected)).to_be(False)
    mock_cloud_obj = Mock(is_logged_in=True)
    type(mock_cloud_obj).username = username_mock
    config = CloudGoogleConfig(
        hass, GACTIONS_SCHEMA({}), "mock-user-id", cloud_prefs_inst, mock_cloud_obj
    )
    expect(config.async_get_agent_users()).to_equal(())
    username_mock.assert_not_called()

    cloud_prefs_inst._prefs["google_connected"] = True
    expect(bool(cloud_prefs_inst.google_connected)).to_be(True)
    mock_cloud_obj = Mock(is_logged_in=True)
    type(mock_cloud_obj).username = username_mock
    config = CloudGoogleConfig(
        hass, GACTIONS_SCHEMA({}), "mock-user-id", cloud_prefs_inst, mock_cloud_obj
    )
    expect(config.async_get_agent_users()).to_equal(("blah",))
    username_mock.assert_called()
