"""Test Alexa config."""

from collections.abc import Generator
import contextlib
from unittest.mock import AsyncMock, Mock, patch

from hass_nabucasa.alexa_api import (
    AlexaApiError,
    AlexaApiNeedsRelinkError,
    AlexaApiNoTokenError,
)
import jwt
from tryke import Depends, expect, fixture, test

from homeassistant.components.alexa import errors
from homeassistant.components.cloud import ALEXA_SCHEMA, alexa_config
from homeassistant.components.cloud.const import (
    DATA_CLOUD,
    PREF_ALEXA_DEFAULT_EXPOSE,
    PREF_ALEXA_ENTITY_CONFIGS,
    PREF_SHOULD_EXPOSE,
)
from homeassistant.components.cloud.prefs import CloudPreferences
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
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import mock_cloud
from ._fixtures import load_homeassistant

from tests.common import async_fire_time_changed
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.test_util.aiohttp import AiohttpClientMocker


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
def cloud_stub() -> Mock:
    """Stub the cloud."""
    return Mock(is_logged_in=True, subscription_expired=False)


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
    """Enable exposing new entities to Alexa."""
    exposed_entities = hass.data[DATA_EXPOSED_ENTITIES]
    exposed_entities.async_set_expose_new_entities("cloud.alexa", expose_new)


def expose_entity(hass: HomeAssistant, entity_id: str, should_expose: bool) -> None:
    """Expose an entity to Alexa."""
    async_expose_entity(hass, "cloud.alexa", entity_id, should_expose)


@contextlib.contextmanager
def patch_sync_helper():
    """Patch sync helper."""
    to_update: list[str] = []
    to_remove: list[str] = []

    def sync_helper(to_upd, to_rem):
        to_update.extend([ent_id for ent_id in to_upd if ent_id not in to_update])
        to_remove.extend([ent_id for ent_id in to_rem if ent_id not in to_remove])
        return True

    with (
        patch("homeassistant.components.cloud.alexa_config.SYNC_DELAY", 0),
        patch(
            "homeassistant.components.cloud.alexa_config.CloudAlexaConfig._sync_helper",
            side_effect=sync_helper,
        ),
    ):
        yield to_update, to_remove


@test
async def alexa_config_expose_entity_prefs(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
    cloud_stub_inst: Mock = Depends(cloud_stub),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test Alexa config should expose using prefs."""
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

    await cloud_prefs_inst.async_update(
        alexa_enabled=True,
        alexa_report_state=False,
    )
    expose_new(hass, True)
    expose_entity(hass, entity_entry5.entity_id, False)
    conf = alexa_config.CloudAlexaConfig(
        hass, ALEXA_SCHEMA({}), "mock-user-id", cloud_prefs_inst, cloud_stub_inst
    )
    expect("alexa" in hass.config.components).to_be(False)
    await conf.async_initialize()
    await hass.async_block_till_done()
    expect("alexa" in hass.config.components).to_be(True)

    expose_entity(hass, "light.kitchen", True)
    expect(bool(conf.should_expose("light.kitchen"))).to_be(True)
    expect(bool(conf.should_expose(entity_entry1.entity_id))).to_be(False)
    expect(bool(conf.should_expose(entity_entry2.entity_id))).to_be(False)
    expect(bool(conf.should_expose(entity_entry3.entity_id))).to_be(False)
    expect(bool(conf.should_expose(entity_entry4.entity_id))).to_be(False)
    expect(bool(conf.should_expose(entity_entry5.entity_id))).to_be(False)
    expect(bool(conf.should_expose(entity_entry6.entity_id))).to_be(True)

    expose_entity(hass, entity_entry5.entity_id, True)
    expect(bool(conf.should_expose(entity_entry5.entity_id))).to_be(True)

    expose_entity(hass, entity_entry5.entity_id, None)
    expect(bool(conf.should_expose(entity_entry5.entity_id))).to_be(False)


@test
async def alexa_config_report_state(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
    cloud_stub_inst: Mock = Depends(cloud_stub),
) -> None:
    """Test Alexa config should expose using prefs."""
    await cloud_prefs_inst.async_update(
        alexa_report_state=False,
    )
    conf = alexa_config.CloudAlexaConfig(
        hass, ALEXA_SCHEMA({}), "mock-user-id", cloud_prefs_inst, cloud_stub_inst
    )
    await conf.async_initialize()
    await conf.set_authorized(True)

    expect(cloud_prefs_inst.alexa_report_state).to_be(False)
    expect(conf.should_report_state).to_be(False)
    expect(conf.is_reporting_states).to_be(False)

    with patch.object(conf, "async_get_access_token", AsyncMock(return_value="hello")):
        await cloud_prefs_inst.async_update(alexa_report_state=True)
        await hass.async_block_till_done()

    expect(cloud_prefs_inst.alexa_report_state).to_be(True)
    expect(conf.should_report_state).to_be(True)
    expect(conf.is_reporting_states).to_be(True)

    await cloud_prefs_inst.async_update(alexa_report_state=False)
    await hass.async_block_till_done()

    expect(cloud_prefs_inst.alexa_report_state).to_be(False)
    expect(conf.should_report_state).to_be(False)
    expect(conf.is_reporting_states).to_be(False)


@test
async def alexa_config_invalidate_token(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test Alexa config should expose using prefs."""
    aioclient_mock.post(
        "https://example/alexa/access_token",
        json={
            "access_token": "mock-token",
            "event_endpoint": "http://example.com/alexa_endpoint",
            "expires_in": 30,
        },
    )
    conf = alexa_config.CloudAlexaConfig(
        hass,
        ALEXA_SCHEMA({}),
        "mock-user-id",
        cloud_prefs_inst,
        Mock(
            servicehandlers_server="example",
            auth=Mock(async_check_token=AsyncMock()),
            websession=async_get_clientsession(hass),
            alexa_api=Mock(
                access_token=AsyncMock(
                    return_value={
                        "access_token": "mock-token",
                        "event_endpoint": "http://example.com/alexa_endpoint",
                        "expires_in": 30,
                    }
                )
            ),
        ),
    )

    token = await conf.async_get_access_token()
    expect(token).to_equal("mock-token")
    expect(len(conf._cloud.alexa_api.access_token.mock_calls)).to_equal(1)

    token = await conf.async_get_access_token()
    expect(token).to_equal("mock-token")
    expect(len(conf._cloud.alexa_api.access_token.mock_calls)).to_equal(1)
    expect(conf._token_valid is not None).to_be(True)
    conf.async_invalidate_access_token()
    expect(conf._token_valid is None).to_be(True)
    token = await conf.async_get_access_token()
    expect(token).to_equal("mock-token")
    expect(len(conf._cloud.alexa_api.access_token.mock_calls)).to_equal(2)


@test.cases(
    test.case(
        "needs_relink",
        lib_exception=AlexaApiNeedsRelinkError("Needs relink"),
        expected_exception=errors.RequireRelink,
    ),
    test.case(
        "unknown_region",
        lib_exception=AlexaApiNeedsRelinkError("UnknownRegion"),
        expected_exception=errors.RequireRelink,
    ),
    test.case(
        "no_token",
        lib_exception=AlexaApiNoTokenError("OtherReason"),
        expected_exception=errors.NoTokenAvailable,
    ),
    test.case(
        "alexa_api_error",
        lib_exception=AlexaApiError("OtherReason"),
        expected_exception=errors.NoTokenAvailable,
    ),
)
async def alexa_config_fail_refresh_token(
    lib_exception: Exception,
    expected_exception: type[Exception],
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test Alexa config failing to refresh token."""
    # Background ChangeReport tasks may surface JSONDecodeError for the
    # empty `text=""` response — that's expected for this test and not a
    # failure. Clear captured loop exceptions at teardown.
    captured = getattr(hass, "_captured_loop_exceptions", None)
    expose_new(hass, True)
    entity_entry = entity_registry.async_get_or_create(
        "fan", "test", "unique", suggested_object_id="test_fan"
    )

    aioclient_mock.post(
        "https://example/alexa/access_token",
        json={
            "access_token": "mock-token",
            "event_endpoint": "http://example.com/alexa_endpoint",
            "expires_in": 30,
        },
    )
    aioclient_mock.post(
        "http://example.com/alexa_endpoint", json={}, status=202
    )
    await cloud_prefs_inst.async_update(
        alexa_report_state=False,
    )
    conf = alexa_config.CloudAlexaConfig(
        hass,
        ALEXA_SCHEMA({}),
        "mock-user-id",
        cloud_prefs_inst,
        Mock(
            servicehandlers_server="example",
            auth=Mock(async_check_token=AsyncMock()),
            websession=async_get_clientsession(hass),
            alexa_api=Mock(
                access_token=AsyncMock(
                    return_value={
                        "access_token": "mock-token",
                        "event_endpoint": "http://example.com/alexa_endpoint",
                        "expires_in": 30,
                    }
                )
            ),
        ),
    )
    await conf.async_initialize()
    await conf.set_authorized(True)

    expect(cloud_prefs_inst.alexa_report_state).to_be(False)
    expect(conf.should_report_state).to_be(False)
    expect(conf.is_reporting_states).to_be(False)

    hass.states.async_set(entity_entry.entity_id, "off")

    await cloud_prefs_inst.async_update(alexa_report_state=True)
    await hass.async_block_till_done()

    expect(cloud_prefs_inst.alexa_report_state).to_be(True)
    expect(conf.should_report_state).to_be(True)
    expect(conf.is_reporting_states).to_be(True)

    hass.states.async_set(entity_entry.entity_id, "on")
    await hass.async_block_till_done()

    conf.async_invalidate_access_token()
    conf._cloud.alexa_api.access_token.side_effect = lib_exception

    hass.states.async_set(entity_entry.entity_id, "off")
    await hass.async_block_till_done()

    expect(cloud_prefs_inst.alexa_report_state).to_be(True)
    expect(conf.should_report_state).to_be(False)
    expect(conf.is_reporting_states).to_be(False)

    async with expect_raises_async(expected_exception):
        await conf.set_authorized(True)

    expect(cloud_prefs_inst.alexa_report_state).to_be(True)
    expect(conf.should_report_state).to_be(False)
    expect(conf.is_reporting_states).to_be(False)

    conf._cloud.alexa_api.access_token.side_effect = None

    await conf.set_authorized(True)
    expect(cloud_prefs_inst.alexa_report_state).to_be(True)
    expect(conf.should_report_state).to_be(True)
    expect(conf.is_reporting_states).to_be(True)

    if captured is not None:
        captured.clear()


@test
async def alexa_update_expose_trigger_sync(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
    cloud_stub_inst: Mock = Depends(cloud_stub),
) -> None:
    """Test Alexa config responds to updating exposed entities."""
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

    hass.states.async_set(binary_sensor_entry.entity_id, "on")
    hass.states.async_set(
        sensor_entry.entity_id,
        "23",
        {"device_class": "temperature", "unit_of_measurement": "°C"},
    )
    hass.states.async_set(light_entry.entity_id, "off")

    await cloud_prefs_inst.async_update(
        alexa_enabled=True,
        alexa_report_state=False,
    )
    conf = alexa_config.CloudAlexaConfig(
        hass, ALEXA_SCHEMA({}), "mock-user-id", cloud_prefs_inst, cloud_stub_inst
    )
    await conf.async_initialize()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    with patch_sync_helper() as (to_update, to_remove):
        expose_entity(hass, light_entry.entity_id, True)
        await hass.async_block_till_done()
        async_fire_time_changed(hass, fire_all=True)
        await hass.async_block_till_done()

    expect(conf._alexa_sync_unsub is None).to_be(True)
    expect(to_update).to_equal([light_entry.entity_id])
    expect(to_remove).to_equal([])

    with patch_sync_helper() as (to_update, to_remove):
        expose_entity(hass, light_entry.entity_id, False)
        expose_entity(hass, binary_sensor_entry.entity_id, True)
        expose_entity(hass, sensor_entry.entity_id, True)
        await hass.async_block_till_done()
        async_fire_time_changed(hass, fire_all=True)
        await hass.async_block_till_done()

    expect(conf._alexa_sync_unsub is None).to_be(True)
    expect(sorted(to_update)).to_equal(
        [binary_sensor_entry.entity_id, sensor_entry.entity_id]
    )
    expect(to_remove).to_equal([light_entry.entity_id])

    with patch_sync_helper() as (to_update, to_remove):
        await cloud_prefs_inst.async_update(
            alexa_enabled=False,
        )
        await hass.async_block_till_done()

    expect(conf._alexa_sync_unsub is None).to_be(True)
    expect(to_update).to_equal([])
    expect(to_remove).to_equal(
        [
            binary_sensor_entry.entity_id,
            sensor_entry.entity_id,
            light_entry.entity_id,
        ]
    )


@test
async def alexa_entity_registry_sync(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(mock_cloud_login_prefs),
) -> None:
    """Test Alexa config responds to entity registry."""
    expose_new(hass, True)

    await alexa_config.CloudAlexaConfig(
        hass,
        ALEXA_SCHEMA({}),
        "mock-user-id",
        cloud_prefs_inst,
        hass.data[DATA_CLOUD],
    ).async_initialize()

    with patch_sync_helper() as (to_update, to_remove):
        entry = entity_registry.async_get_or_create(
            "light", "test", "unique", suggested_object_id="kitchen"
        )
        await hass.async_block_till_done()

    expect(to_update).to_equal([entry.entity_id])
    expect(to_remove).to_equal([])

    with patch_sync_helper() as (to_update, to_remove):
        hass.bus.async_fire(
            er.EVENT_ENTITY_REGISTRY_UPDATED,
            {"action": "remove", "entity_id": entry.entity_id},
        )
        await hass.async_block_till_done()

    expect(to_update).to_equal([])
    expect(to_remove).to_equal([entry.entity_id])

    with patch_sync_helper() as (to_update, to_remove):
        hass.bus.async_fire(
            er.EVENT_ENTITY_REGISTRY_UPDATED,
            {
                "action": "update",
                "entity_id": entry.entity_id,
                "changes": ["entity_id"],
                "old_entity_id": "light.living_room",
            },
        )
        await hass.async_block_till_done()

    expect(to_update).to_equal([entry.entity_id])
    expect(to_remove).to_equal(["light.living_room"])

    with patch_sync_helper() as (to_update, to_remove):
        hass.bus.async_fire(
            er.EVENT_ENTITY_REGISTRY_UPDATED,
            {"action": "update", "entity_id": entry.entity_id, "changes": ["icon"]},
        )
        await hass.async_block_till_done()

    expect(to_update).to_equal([])
    expect(to_remove).to_equal([])


@test
async def alexa_update_report_state(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
    cloud_stub_inst: Mock = Depends(cloud_stub),
) -> None:
    """Test Alexa config responds to reporting state."""
    await cloud_prefs_inst.async_update(
        alexa_report_state=False,
    )
    conf = alexa_config.CloudAlexaConfig(
        hass, ALEXA_SCHEMA({}), "mock-user-id", cloud_prefs_inst, cloud_stub_inst
    )
    await conf.async_initialize()
    await conf.set_authorized(True)

    with (
        patch(
            "homeassistant.components.cloud.alexa_config.CloudAlexaConfig.async_sync_entities",
        ) as mock_sync,
        patch(
            "homeassistant.components.cloud.alexa_config.CloudAlexaConfig.async_enable_proactive_mode",
        ),
    ):
        await cloud_prefs_inst.async_update(alexa_report_state=True)
        await hass.async_block_till_done()

    expect(len(mock_sync.mock_calls)).to_equal(1)


@test
async def enabled_requires_valid_sub(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(mock_cloud_setup),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
) -> None:
    """Test that alexa config enabled requires a valid Cloud sub."""
    _set_expired_cloud_login(hass)

    expect(bool(cloud_prefs_inst.alexa_enabled)).to_be(True)
    expect(bool(hass.data[DATA_CLOUD].is_logged_in)).to_be(True)
    expect(bool(hass.data[DATA_CLOUD].subscription_expired)).to_be(True)

    config = alexa_config.CloudAlexaConfig(
        hass,
        ALEXA_SCHEMA({}),
        "mock-user-id",
        cloud_prefs_inst,
        hass.data[DATA_CLOUD],
    )

    expect(bool(config.enabled)).to_be(False)


@test
async def alexa_handle_logout(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
    cloud_stub_inst: Mock = Depends(cloud_stub),
) -> None:
    """Test Alexa config responds to logging out."""
    aconf = alexa_config.CloudAlexaConfig(
        hass, ALEXA_SCHEMA({}), "mock-user-id", cloud_prefs_inst, cloud_stub_inst
    )

    await aconf.async_initialize()

    with patch(
        "homeassistant.components.alexa.config.async_enable_proactive_mode",
        return_value=Mock(),
    ) as mock_enable:
        await aconf.async_enable_proactive_mode()
        await hass.async_block_till_done()

    expect(len(aconf._on_deinitialize)).to_equal(5)

    await cloud_prefs_inst.get_cloud_user()

    cloud_stub_inst.is_logged_in = False
    with patch.object(
        cloud_stub_inst.auth,
        "async_check_token",
        side_effect=AssertionError("Should not be called"),
    ):
        await cloud_prefs_inst.async_set_username(None)
        aconf.async_deinitialize()
        await hass.async_block_till_done()
        expect(bool(aconf._on_deinitialize)).to_be(False)

    expect(len(mock_enable.return_value.mock_calls)).to_equal(1)


@test.cases(
    test.case("v1", alexa_settings_version=1),
    test.case("v2", alexa_settings_version=2),
)
async def alexa_config_migrate_expose_entity_prefs(
    alexa_settings_version: int,
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
    cloud_stub_inst: Mock = Depends(cloud_stub),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test migrating Alexa entity config."""
    hass.set_state(CoreState.starting)

    hass.states.async_set("light.state_only", "on")
    entity_exposed = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_exposed",
        suggested_object_id="exposed",
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
        alexa_enabled=True,
        alexa_report_state=False,
        alexa_settings_version=alexa_settings_version,
    )
    expose_entity(hass, entity_migrated.entity_id, False)

    cloud_prefs_inst._prefs[PREF_ALEXA_ENTITY_CONFIGS]["light.unknown"] = {
        PREF_SHOULD_EXPOSE: True
    }
    cloud_prefs_inst._prefs[PREF_ALEXA_ENTITY_CONFIGS]["light.state_only"] = {
        PREF_SHOULD_EXPOSE: False
    }
    cloud_prefs_inst._prefs[PREF_ALEXA_ENTITY_CONFIGS][entity_exposed.entity_id] = {
        PREF_SHOULD_EXPOSE: True
    }
    cloud_prefs_inst._prefs[PREF_ALEXA_ENTITY_CONFIGS][entity_migrated.entity_id] = {
        PREF_SHOULD_EXPOSE: True
    }
    conf = alexa_config.CloudAlexaConfig(
        hass, ALEXA_SCHEMA({}), "mock-user-id", cloud_prefs_inst, cloud_stub_inst
    )
    await conf.async_initialize()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    expect(async_get_entity_settings(hass, "light.unknown")).to_equal(
        {"cloud.alexa": {"should_expose": True}}
    )
    expect(async_get_entity_settings(hass, "light.state_only")).to_equal(
        {"cloud.alexa": {"should_expose": False}}
    )
    expect(async_get_entity_settings(hass, entity_exposed.entity_id)).to_equal(
        {"cloud.alexa": {"should_expose": True}}
    )
    expect(async_get_entity_settings(hass, entity_migrated.entity_id)).to_equal(
        {"cloud.alexa": {"should_expose": True}}
    )
    expect(async_get_entity_settings(hass, entity_config.entity_id)).to_equal(
        {"cloud.alexa": {"should_expose": False}}
    )
    expect(async_get_entity_settings(hass, entity_default.entity_id)).to_equal(
        {"cloud.alexa": {"should_expose": True}}
    )
    expect(async_get_entity_settings(hass, entity_blocked.entity_id)).to_equal(
        {"cloud.alexa": {"should_expose": False}}
    )


@test
async def alexa_config_migrate_expose_entity_prefs_v2_no_exposed(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test migrating Alexa entity config from v2 to v3 when no entity is exposed."""
    hass.set_state(CoreState.starting)

    hass.states.async_set("light.state_only", "on")
    entity_migrated = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_migrated",
        suggested_object_id="migrated",
    )
    await cloud_prefs_inst.async_update(
        alexa_enabled=True,
        alexa_report_state=False,
        alexa_settings_version=2,
    )
    expose_entity(hass, "light.state_only", False)
    expose_entity(hass, entity_migrated.entity_id, False)

    cloud_prefs_inst._prefs[PREF_ALEXA_ENTITY_CONFIGS]["light.state_only"] = {
        PREF_SHOULD_EXPOSE: True
    }
    cloud_prefs_inst._prefs[PREF_ALEXA_ENTITY_CONFIGS][entity_migrated.entity_id] = {
        PREF_SHOULD_EXPOSE: True
    }
    conf = alexa_config.CloudAlexaConfig(
        hass,
        ALEXA_SCHEMA({}),
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
        {"cloud.alexa": {"should_expose": True}}
    )
    expect(async_get_entity_settings(hass, entity_migrated.entity_id)).to_equal(
        {"cloud.alexa": {"should_expose": True}}
    )


@test
async def alexa_config_migrate_expose_entity_prefs_v2_exposed(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test migrating Alexa entity config from v2 to v3 when an entity is exposed."""
    hass.set_state(CoreState.starting)

    hass.states.async_set("light.state_only", "on")
    entity_migrated = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_migrated",
        suggested_object_id="migrated",
    )
    await cloud_prefs_inst.async_update(
        alexa_enabled=True,
        alexa_report_state=False,
        alexa_settings_version=2,
    )
    expose_entity(hass, "light.state_only", False)
    expose_entity(hass, entity_migrated.entity_id, True)

    cloud_prefs_inst._prefs[PREF_ALEXA_ENTITY_CONFIGS]["light.state_only"] = {
        PREF_SHOULD_EXPOSE: True
    }
    cloud_prefs_inst._prefs[PREF_ALEXA_ENTITY_CONFIGS][entity_migrated.entity_id] = {
        PREF_SHOULD_EXPOSE: True
    }
    conf = alexa_config.CloudAlexaConfig(
        hass,
        ALEXA_SCHEMA({}),
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
        {"cloud.alexa": {"should_expose": False}}
    )
    expect(async_get_entity_settings(hass, entity_migrated.entity_id)).to_equal(
        {"cloud.alexa": {"should_expose": True}}
    )


@test
async def alexa_config_migrate_expose_entity_prefs_default_none(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
    cloud_stub_inst: Mock = Depends(cloud_stub),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test migrating Alexa entity config."""
    hass.set_state(CoreState.starting)

    entity_default = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_default",
        suggested_object_id="default",
    )

    await cloud_prefs_inst.async_update(
        alexa_enabled=True,
        alexa_report_state=False,
        alexa_settings_version=1,
    )

    cloud_prefs_inst._prefs[PREF_ALEXA_DEFAULT_EXPOSE] = None
    conf = alexa_config.CloudAlexaConfig(
        hass, ALEXA_SCHEMA({}), "mock-user-id", cloud_prefs_inst, cloud_stub_inst
    )
    await conf.async_initialize()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    expect(async_get_entity_settings(hass, entity_default.entity_id)).to_equal(
        {"cloud.alexa": {"should_expose": True}}
    )


@test
async def alexa_config_migrate_expose_entity_prefs_default(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_prefs_inst: CloudPreferences = Depends(cloud_prefs),
    cloud_stub_inst: Mock = Depends(cloud_stub),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test migrating Alexa entity config."""
    hass.set_state(CoreState.starting)

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
        alexa_enabled=True,
        alexa_report_state=False,
        alexa_settings_version=1,
    )

    cloud_prefs_inst._prefs[PREF_ALEXA_DEFAULT_EXPOSE] = [
        "binary_sensor",
        "light",
        "sensor",
        "water_heater",
    ]
    conf = alexa_config.CloudAlexaConfig(
        hass, ALEXA_SCHEMA({}), "mock-user-id", cloud_prefs_inst, cloud_stub_inst
    )
    await conf.async_initialize()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    expect(async_get_entity_settings(hass, binary_sensor_supported.entity_id)).to_equal(
        {"cloud.alexa": {"should_expose": True}}
    )
    expect(
        async_get_entity_settings(hass, binary_sensor_unsupported.entity_id)
    ).to_equal({"cloud.alexa": {"should_expose": False}})
    expect(async_get_entity_settings(hass, light.entity_id)).to_equal(
        {"cloud.alexa": {"should_expose": True}}
    )
    expect(async_get_entity_settings(hass, sensor_supported.entity_id)).to_equal(
        {"cloud.alexa": {"should_expose": True}}
    )
    expect(async_get_entity_settings(hass, sensor_unsupported.entity_id)).to_equal(
        {"cloud.alexa": {"should_expose": False}}
    )
    expect(async_get_entity_settings(hass, water_heater.entity_id)).to_equal(
        {"cloud.alexa": {"should_expose": False}}
    )
