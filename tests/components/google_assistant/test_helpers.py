"""Test Google Assistant helpers."""

from datetime import timedelta
from http import HTTPStatus
from unittest.mock import Mock, call, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.google_assistant import helpers
from homeassistant.components.google_assistant.const import (
    EVENT_COMMAND_RECEIVED,
    NOT_EXPOSE_LOCAL,
    SOURCE_CLOUD,
    SOURCE_LOCAL,
    STORE_GOOGLE_LOCAL_WEBHOOK_ID,
)
from homeassistant.components.matter import MatterDeviceInfo
from homeassistant.core import HomeAssistant, State
from homeassistant.core_config import async_process_ha_core_config
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from . import MockConfig
from ._fixtures import (
    ClientSessionGenerator,
    LogCapture,
    caplog_fx,
    device_registry_fx,
    entity_registry_fx,
    hass_client_fx,
    hass_fixture,
)

from tests.common import MockConfigEntry, async_capture_events, async_mock_service


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def google_entity_sync_serialize_with_local_sdk(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test sync serialize attributes of a GoogleEntity."""
    hass.states.async_set("light.ceiling_lights", "off")
    hass.config.api = Mock(port=1234, local_ip="192.168.123.123", use_ssl=False)
    await async_process_ha_core_config(
        hass,
        {"external_url": "https://hostname:1234"},
    )

    hass.http = Mock(server_port=1234)
    config = MockConfig(
        hass=hass,
        agent_user_ids={
            "mock-user-id": {
                STORE_GOOGLE_LOCAL_WEBHOOK_ID: "mock-webhook-id",
            },
        },
    )
    entity = helpers.GoogleEntity(hass, config, hass.states.get("light.ceiling_lights"))

    serialized = entity.sync_serialize(None, "mock-uuid")
    expect("otherDeviceIds" not in serialized).to_be(True)
    expect("customData" not in serialized).to_be(True)

    config.async_enable_local_sdk()

    serialized = entity.sync_serialize("mock-user-id", "abcdef")
    expect(serialized["otherDeviceIds"]).to_equal([{"deviceId": "light.ceiling_lights"}])
    expect(serialized["customData"]).to_equal(
        {
            "httpPort": 1234,
            "webhookId": "mock-webhook-id",
            "uuid": "abcdef",
        }
    )

    for device_type in NOT_EXPOSE_LOCAL:
        with patch(
            "homeassistant.components.google_assistant.helpers.get_google_type",
            return_value=device_type,
        ):
            serialized = entity.sync_serialize(None, "mock-uuid")
            expect("otherDeviceIds" not in serialized).to_be(True)
            expect("customData" not in serialized).to_be(True)


@test
async def google_entity_sync_serialize_with_matter(
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test sync serialize attributes of a GoogleEntity that is also a Matter device."""
    entry = MockConfigEntry()
    entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        manufacturer="Someone",
        model="Some model",
        sw_version="Some Version",
        identifiers={("matter", "12345678")},
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity = entity_registry.async_get_or_create(
        "light",
        "test",
        "1235",
        suggested_object_id="ceiling_lights",
        device_id=device.id,
    )
    hass.states.async_set("light.ceiling_lights", "off")

    entity = helpers.GoogleEntity(
        hass, MockConfig(hass=hass), hass.states.get("light.ceiling_lights")
    )

    serialized = entity.sync_serialize(None, "mock-uuid")
    expect("matterUniqueId" not in serialized).to_be(True)
    expect("matterOriginalVendorId" not in serialized).to_be(True)
    expect("matterOriginalProductId" not in serialized).to_be(True)

    hass.config.components.add("matter")

    with patch(
        "homeassistant.components.matter.get_matter_device_info",
        return_value=MatterDeviceInfo(
            unique_id="mock-unique-id",
            vendor_id="mock-vendor-id",
            product_id="mock-product-id",
        ),
    ):
        serialized = entity.sync_serialize("mock-user-id", "abcdef")

    expect(serialized["matterUniqueId"]).to_equal("mock-unique-id")
    expect(serialized["matterOriginalVendorId"]).to_equal("mock-vendor-id")
    expect(serialized["matterOriginalProductId"]).to_equal("mock-product-id")


@test
async def config_local_sdk(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test the local SDK."""
    command_events = async_capture_events(hass, EVENT_COMMAND_RECEIVED)
    turn_on_calls = async_mock_service(hass, "light", "turn_on")
    hass.states.async_set("light.ceiling_lights", "off")

    expect(await async_setup_component(hass, "webhook", {})).to_be(True)

    config = MockConfig(
        hass=hass,
        agent_user_ids={
            "mock-user-id": {
                STORE_GOOGLE_LOCAL_WEBHOOK_ID: "mock-webhook-id",
            },
        },
    )

    client = await hass_client()

    expect(config.is_local_connected).to_be(False)
    config.async_enable_local_sdk()
    expect(config.is_local_connected).to_be(False)

    resp = await client.post(
        "/api/webhook/mock-webhook-id",
        json={
            "inputs": [
                {
                    "context": {"locale_country": "US", "locale_language": "en"},
                    "intent": "action.devices.EXECUTE",
                    "payload": {
                        "commands": [
                            {
                                "devices": [{"id": "light.ceiling_lights"}],
                                "execution": [
                                    {
                                        "command": "action.devices.commands.OnOff",
                                        "params": {"on": True},
                                    }
                                ],
                            }
                        ],
                        "structureData": {},
                    },
                }
            ],
            "requestId": "mock-req-id",
        },
    )

    expect(config.is_local_connected).to_be(True)
    with patch(
        "homeassistant.components.google_assistant.helpers.utcnow",
        return_value=dt_util.utcnow() + timedelta(seconds=90),
    ):
        expect(config.is_local_connected).to_be(False)

    expect(resp.status).to_equal(HTTPStatus.OK)
    result = await resp.json()
    expect(result["requestId"]).to_equal("mock-req-id")

    expect(len(command_events)).to_equal(1)
    expect(command_events[0].context.user_id).to_equal("mock-user-id")

    expect(len(turn_on_calls)).to_equal(1)
    expect(turn_on_calls[0].context is command_events[0].context).to_be(True)

    config.async_disable_local_sdk()

    # Webhook is no longer active
    resp = await client.post("/api/webhook/mock-webhook-id")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(await resp.read()).to_equal(b"")


@test
async def config_local_sdk_if_disabled(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test the local SDK."""
    expect(await async_setup_component(hass, "webhook", {})).to_be(True)

    config = MockConfig(
        hass=hass,
        agent_user_ids={
            "mock-user-id": {
                STORE_GOOGLE_LOCAL_WEBHOOK_ID: "mock-webhook-id",
            },
        },
        enabled=False,
    )
    expect(config.is_local_sdk_active).to_be(False)

    client = await hass_client()

    config.async_enable_local_sdk()
    expect(config.is_local_sdk_active).to_be(True)

    resp = await client.post(
        "/api/webhook/mock-webhook-id", json={"requestId": "mock-req-id"}
    )
    expect(resp.status).to_equal(HTTPStatus.OK)
    result = await resp.json()
    expect(result).to_equal(
        {
            "payload": {"errorCode": "deviceTurnedOff"},
            "requestId": "mock-req-id",
        }
    )

    config.async_disable_local_sdk()
    expect(config.is_local_sdk_active).to_be(False)

    # Webhook is no longer active
    resp = await client.post("/api/webhook/mock-webhook-id")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(await resp.read()).to_equal(b"")


@test
async def config_local_sdk_if_ssl_enabled(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test the local SDK is not enabled when SSL is enabled."""
    expect(await async_setup_component(hass, "webhook", {})).to_be(True)
    hass.config.api.use_ssl = True

    config = MockConfig(
        hass=hass,
        agent_user_ids={
            "mock-user-id": {
                STORE_GOOGLE_LOCAL_WEBHOOK_ID: "mock-webhook-id",
            },
        },
        enabled=False,
    )
    expect(config.is_local_sdk_active).to_be(False)

    client = await hass_client()

    config.async_enable_local_sdk()
    expect(config.is_local_sdk_active).to_be(False)

    # Webhook should not be activated
    resp = await client.post("/api/webhook/mock-webhook-id")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(await resp.read()).to_equal(b"")


@test
async def agent_user_id_connect() -> None:
    """Test the connection and disconnection of users."""
    config = MockConfig()
    store = config._store

    await config.async_connect_agent_user("agent_2")
    expect(store.add_agent_user_id.call_args).to_equal(call("agent_2"))

    await config.async_connect_agent_user("agent_1")
    expect(store.add_agent_user_id.call_args).to_equal(call("agent_1"))

    await config.async_disconnect_agent_user("agent_2")
    expect(store.pop_agent_user_id.call_args).to_equal(call("agent_2"))

    await config.async_disconnect_agent_user("agent_1")
    expect(store.pop_agent_user_id.call_args).to_equal(call("agent_1"))


@test.cases(
    test.case("empty", agents=set()),
    test.case("one", agents={"1"}),
    test.case("two", agents={"1", "2"}),
)
async def report_state_all(agents: set[str]) -> None:
    """Test sync of all states."""
    config = MockConfig(agent_user_ids=agents)
    data = {}
    with patch.object(config, "async_report_state") as mock:
        await config.async_report_state_all(data)
        expect(sorted(mock.mock_calls)).to_equal(
            sorted(call(data, agent) for agent in agents)
        )


@test.cases(
    test.case("empty", agents=set()),
    test.case("one", agents={"1"}),
    test.case("two", agents={"1", "2"}),
)
async def sync_entities(agents: set[str]) -> None:
    """Test sync of all entities."""
    config = MockConfig(agent_user_ids=agents)
    with patch.object(
        config, "async_sync_entities", return_value=HTTPStatus.NO_CONTENT
    ) as mock:
        await config.async_sync_entities_all()
        expect(sorted(mock.mock_calls)).to_equal(
            sorted(call(agent) for agent in agents)
        )


@test.cases(
    test.case("empty", agents=set()),
    test.case("one", agents={"1"}),
    test.case("two", agents={"1", "2"}),
)
async def sync_notifications(agents: set[str]) -> None:
    """Test sync of notifications."""
    config = MockConfig(agent_user_ids=agents)
    with patch.object(
        config, "async_sync_notification", return_value=HTTPStatus.NO_CONTENT
    ) as mock:
        await config.async_sync_notification_all("1234", {})
        expect(not agents or (bool(mock.mock_calls) and bool(agents))).to_be(True)


@test.cases(
    test.case("empty", agents={}, result=204),
    test.case("one", agents={"1": 200}, result=200),
    test.case("two", agents={"1": 200, "2": 300}, result=300),
)
async def sync_entities_all(agents: dict[str, int], result: int) -> None:
    """Test sync entities ."""
    config = MockConfig(agent_user_ids=set(agents.keys()))
    with patch.object(
        config,
        "async_sync_entities",
        side_effect=lambda agent_user_id: agents[agent_user_id],
    ) as mock:
        res = await config.async_sync_entities_all()
        expect(sorted(mock.mock_calls)).to_equal(
            sorted(call(agent) for agent in agents)
        )
        expect(res).to_equal(result)


@test
def supported_features_string(
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test bad supported features."""
    entity = helpers.GoogleEntity(
        None,
        MockConfig(),
        State("test.entity_id", "on", {"supported_features": "invalid"}),
    )
    expect(entity.is_supported()).to_be(False)
    expect(
        "Entity test.entity_id contains invalid supported_features value invalid"
        in caplog.text
    ).to_be(True)


@test
def request_data() -> None:
    """Test request data properties."""
    config = MockConfig()
    data = helpers.RequestData(
        config, "test_user", SOURCE_LOCAL, "test_request_id", None
    )
    expect(data.is_local_request).to_be(True)

    data = helpers.RequestData(
        config, "test_user", SOURCE_CLOUD, "test_request_id", None
    )
    expect(data.is_local_request).to_be(False)


@test
async def config_local_sdk_allow_min_version(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test the local SDK."""
    version = str(helpers.LOCAL_SDK_MIN_VERSION)
    expect(await async_setup_component(hass, "webhook", {})).to_be(True)

    config = MockConfig(
        hass=hass,
        agent_user_ids={
            "mock-user-id": {
                STORE_GOOGLE_LOCAL_WEBHOOK_ID: "mock-webhook-id",
            },
        },
    )

    client = await hass_client()

    expect(config._local_sdk_version_warn).to_be(False)
    config.async_enable_local_sdk()

    await client.post(
        "/api/webhook/mock-webhook-id",
        headers={helpers.LOCAL_SDK_VERSION_HEADER: version},
        json={
            "inputs": [
                {
                    "context": {"locale_country": "US", "locale_language": "en"},
                    "intent": "action.devices.SYNC",
                }
            ],
            "requestId": "mock-req-id",
        },
    )
    expect(config._local_sdk_version_warn).to_be(False)
    expect(
        (
            f"Local SDK version is too old ({version}), check documentation on how "
            "to update to the latest version"
        )
        not in caplog.text
    ).to_be(True)


@test.cases(
    test.case("none", version=None),
    test.case("old", version="2.1.4"),
)
async def config_local_sdk_warn_version(
    version: str | None,
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test the local SDK."""
    expect(await async_setup_component(hass, "webhook", {})).to_be(True)

    config = MockConfig(
        hass=hass,
        agent_user_ids={
            "mock-user-id": {
                STORE_GOOGLE_LOCAL_WEBHOOK_ID: "mock-webhook-id",
            },
        },
    )

    client = await hass_client()

    expect(config._local_sdk_version_warn).to_be(False)
    config.async_enable_local_sdk()

    headers = {}
    if version:
        headers[helpers.LOCAL_SDK_VERSION_HEADER] = version

    await client.post(
        "/api/webhook/mock-webhook-id",
        headers=headers,
        json={
            "inputs": [
                {
                    "context": {"locale_country": "US", "locale_language": "en"},
                    "intent": "action.devices.SYNC",
                }
            ],
            "requestId": "mock-req-id",
        },
    )
    expect(config._local_sdk_version_warn).to_be(True)
    expect(
        (
            f"Local SDK version is too old ({version}), check documentation on how "
            "to update to the latest version"
        )
        in caplog.text
    ).to_be(True)


@test
def async_get_entities_cached(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test async_get_entities is cached."""
    config = MockConfig()

    hass.states.async_set("light.ceiling_lights", "off")
    hass.states.async_set("light.bed_light", "off")
    hass.states.async_set("not_supported.not_supported", "off")

    google_entities = helpers.async_get_entities(hass, config)
    expect(len(google_entities)).to_equal(2)
    expect(config.is_supported_cache).to_equal(
        {
            "light.bed_light": (None, True),
            "light.ceiling_lights": (None, True),
            "not_supported.not_supported": (None, False),
        }
    )

    with patch(
        "homeassistant.components.google_assistant.helpers.GoogleEntity.traits",
        return_value=RuntimeError("Should not be called"),
    ):
        google_entities = helpers.async_get_entities(hass, config)

    expect(len(google_entities)).to_equal(2)
    expect(config.is_supported_cache).to_equal(
        {
            "light.bed_light": (None, True),
            "light.ceiling_lights": (None, True),
            "not_supported.not_supported": (None, False),
        }
    )

    hass.states.async_set("light.new", "on")
    google_entities = helpers.async_get_entities(hass, config)

    expect(len(google_entities)).to_equal(3)
    expect(config.is_supported_cache).to_equal(
        {
            "light.bed_light": (None, True),
            "light.new": (None, True),
            "light.ceiling_lights": (None, True),
            "not_supported.not_supported": (None, False),
        }
    )

    hass.states.async_set("light.new", "on", {"supported_features": 1})
    google_entities = helpers.async_get_entities(hass, config)

    expect(len(google_entities)).to_equal(3)
    expect(config.is_supported_cache).to_equal(
        {
            "light.bed_light": (None, True),
            "light.new": (1, True),
            "light.ceiling_lights": (None, True),
            "not_supported.not_supported": (None, False),
        }
    )
