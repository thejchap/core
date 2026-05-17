"""Test config flow."""

from collections.abc import Generator
from http import HTTPStatus
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from aiohasupervisor import SupervisorError, SupervisorNotFoundError
from aiohasupervisor.models import Discovery
from aiohttp.test_utils import TestClient
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.mqtt import DOMAIN as MQTT_DOMAIN
from homeassistant.config_entries import ConfigEntries
from homeassistant.const import EVENT_HOMEASSISTANT_START, EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery_flow import DiscoveryKey
from homeassistant.helpers.service_info.hassio import HassioServiceInfo
from homeassistant.setup import async_setup_component

from ._fixtures import (
    addon_installed,
    get_addon_discovery_info,
    get_discovery_message,
    hassio_client,
    supervisor_root_info,
)

from tests.common import (
    MockConfigEntry,
    MockModule,
    MockUser,
    mock_config_flow,
    mock_integration,
    mock_platform,
)
from tests.hass_fixtures import (
    caplog as caplog_fx,
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fx,
)
from tests.hass_tryke_helpers import mock_async_zeroconf


@fixture
def _trigger_executor(_network=Depends(mock_async_zeroconf)) -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@fixture
def mock_mqtt(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[type[config_entries.ConfigFlow]]:
    """Mock the MQTT integration's config flow."""
    mock_integration(hass, MockModule(MQTT_DOMAIN))
    mock_platform(hass, f"{MQTT_DOMAIN}.config_flow", None)

    class MqttFlow(config_entries.ConfigFlow):
        """Test flow."""

        VERSION = 1

        async_step_hassio = AsyncMock(return_value={"type": "abort"})

    with mock_config_flow(MQTT_DOMAIN, MqttFlow):
        yield MqttFlow


@test
async def hassio_discovery_startup(
    hass: HomeAssistant = Depends(hass_fixture),
    _hassio_client: TestClient = Depends(hassio_client),
    mock_mqtt: type[config_entries.ConfigFlow] = Depends(mock_mqtt),
    addon_installed: AsyncMock = Depends(addon_installed),
    get_addon_discovery_info: AsyncMock = Depends(get_addon_discovery_info),
) -> None:
    """Test startup and discovery after event."""
    get_addon_discovery_info.return_value = [
        Discovery(
            addon="mosquitto",
            service="mqtt",
            uuid=(uuid := uuid4()),
            config={
                "broker": "mock-broker",
                "port": 1883,
                "username": "mock-user",
                "password": "mock-pass",
                "protocol": "3.1.1",
            },
        )
    ]
    addon_installed.return_value.name = "Mosquitto Test"

    expect(get_addon_discovery_info.call_count).to_equal(0)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()
    expect(get_addon_discovery_info.call_count).to_equal(1)
    expect(mock_mqtt.async_step_hassio.called).to_equal(True)
    mock_mqtt.async_step_hassio.assert_called_with(
        HassioServiceInfo(
            config={
                "broker": "mock-broker",
                "port": 1883,
                "username": "mock-user",
                "password": "mock-pass",
                "protocol": "3.1.1",
                "addon": "Mosquitto Test",
            },
            name="Mosquitto Test",
            slug="mosquitto",
            uuid=uuid.hex,
        )
    )


@test
async def hassio_discovery_startup_done(
    hass: HomeAssistant = Depends(hass_fixture),
    _hassio_client: TestClient = Depends(hassio_client),
    mock_mqtt: type[config_entries.ConfigFlow] = Depends(mock_mqtt),
    addon_installed: AsyncMock = Depends(addon_installed),
    get_addon_discovery_info: AsyncMock = Depends(get_addon_discovery_info),
    supervisor_root_info: AsyncMock = Depends(supervisor_root_info),
) -> None:
    """Test startup and discovery with hass discovery."""
    get_addon_discovery_info.return_value = [
        Discovery(
            addon="mosquitto",
            service="mqtt",
            uuid=(uuid := uuid4()),
            config={
                "broker": "mock-broker",
                "port": 1883,
                "username": "mock-user",
                "password": "mock-pass",
                "protocol": "3.1.1",
            },
        )
    ]
    addon_installed.return_value.name = "Mosquitto Test"

    supervisor_root_info.side_effect = SupervisorError()
    await hass.async_start()
    await async_setup_component(hass, "hassio", {})
    await hass.async_block_till_done()

    expect(get_addon_discovery_info.call_count).to_equal(1)
    expect(mock_mqtt.async_step_hassio.called).to_equal(True)
    mock_mqtt.async_step_hassio.assert_called_with(
        HassioServiceInfo(
            config={
                "broker": "mock-broker",
                "port": 1883,
                "username": "mock-user",
                "password": "mock-pass",
                "protocol": "3.1.1",
                "addon": "Mosquitto Test",
            },
            name="Mosquitto Test",
            slug="mosquitto",
            uuid=uuid.hex,
        )
    )


@test
async def hassio_discovery_webhook(
    hass: HomeAssistant = Depends(hass_fixture),
    hassio_client: TestClient = Depends(hassio_client),
    mock_mqtt: type[config_entries.ConfigFlow] = Depends(mock_mqtt),
    addon_installed: AsyncMock = Depends(addon_installed),
    get_discovery_message: AsyncMock = Depends(get_discovery_message),
) -> None:
    """Test discovery webhook."""
    get_discovery_message.return_value = Discovery(
        addon="mosquitto",
        service="mqtt",
        uuid=(uuid := uuid4()),
        config={
            "broker": "mock-broker",
            "port": 1883,
            "username": "mock-user",
            "password": "mock-pass",
            "protocol": "3.1.1",
        },
    )
    addon_installed.return_value.name = "Mosquitto Test"

    resp = await hassio_client.post(
        f"/api/hassio_push/discovery/{uuid!s}",
        json={"addon": "mosquitto", "service": "mqtt", "uuid": str(uuid)},
    )
    await hass.async_block_till_done()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(get_discovery_message.call_count).to_equal(1)
    expect(mock_mqtt.async_step_hassio.called).to_equal(True)
    mock_mqtt.async_step_hassio.assert_called_with(
        HassioServiceInfo(
            config={
                "broker": "mock-broker",
                "port": 1883,
                "username": "mock-user",
                "password": "mock-pass",
                "protocol": "3.1.1",
                "addon": "Mosquitto Test",
            },
            name="Mosquitto Test",
            slug="mosquitto",
            uuid=uuid.hex,
        )
    )


@test
async def hassio_discovery_webhook_non_admin(
    hass: HomeAssistant = Depends(hass_fixture),
    hassio_client: TestClient = Depends(hassio_client),
    mock_mqtt: type[config_entries.ConfigFlow] = Depends(mock_mqtt),
    addon_installed: AsyncMock = Depends(addon_installed),
    get_discovery_message: AsyncMock = Depends(get_discovery_message),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test discovery webhook fails for non-admin users."""
    addon_installed.return_value.name = "Mosquitto Test"

    await hass.async_block_till_done()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    hass_admin_user.groups = []
    get_discovery_message.reset_mock()
    uuid = uuid4()

    resp = await hassio_client.post(
        f"/api/hassio_push/discovery/{uuid!s}",
        json={"addon": "mosquitto", "service": "mqtt", "uuid": str(uuid)},
    )
    await hass.async_block_till_done()

    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)
    get_discovery_message.assert_not_called()
    mock_mqtt.async_step_hassio.assert_not_called()


TEST_UUID = str(uuid4())


@test
async def delete_hassio_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
    hassio_client: TestClient = Depends(hassio_client),
    _addon_installed: AsyncMock = Depends(addon_installed),
    _get_addon_discovery_info: AsyncMock = Depends(get_addon_discovery_info),
    get_discovery_message: AsyncMock = Depends(get_discovery_message),
) -> None:
    """Test deleting a discovery item removes the config entry."""
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    entry = MockConfigEntry(
        domain=MQTT_DOMAIN,
        discovery_keys={
            "hassio": (DiscoveryKey(domain="hassio", key=TEST_UUID, version=1),)
        },
        unique_id=(uuid := uuid4()).hex,
        state=config_entries.ConfigEntryState.LOADED,
        source=config_entries.SOURCE_HASSIO,
    )
    entry.add_to_hass(hass)

    get_discovery_message.side_effect = SupervisorNotFoundError()

    with patch.object(ConfigEntries, "async_remove") as mock_remove:
        resp = await hassio_client.delete(
            f"/api/hassio_push/discovery/{uuid.hex}",
            json={"service": "mqtt", "uuid": uuid.hex},
        )
        await hass.async_block_till_done()

        expect(resp.status).to_equal(HTTPStatus.OK)
        get_discovery_message.assert_called_once_with(uuid)
        mock_remove.assert_called_once_with(entry.entry_id)


@test
async def delete_hassio_discovery_fails_when_discovery_exists(
    hass: HomeAssistant = Depends(hass_fixture),
    hassio_client: TestClient = Depends(hassio_client),
    _addon_installed: AsyncMock = Depends(addon_installed),
    _get_addon_discovery_info: AsyncMock = Depends(get_addon_discovery_info),
    get_discovery_message: AsyncMock = Depends(get_discovery_message),
    caplog=Depends(caplog_fx),
) -> None:
    """Test deleting a discovery item fails when discovery exists."""
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    entry = MockConfigEntry(
        domain=MQTT_DOMAIN,
        discovery_keys={
            "hassio": (DiscoveryKey(domain="hassio", key=TEST_UUID, version=1),)
        },
        unique_id=(uuid := uuid4()).hex,
        state=config_entries.ConfigEntryState.LOADED,
        source=config_entries.SOURCE_HASSIO,
    )
    entry.add_to_hass(hass)

    get_discovery_message.return_value = Discovery(
        addon="mosquitto",
        service="mqtt",
        uuid=(uuid := uuid4()),
        config={
            "broker": "mock-broker",
            "port": 1883,
            "username": "mock-user",
            "password": "mock-pass",
            "protocol": "3.1.1",
        },
    )

    with patch.object(ConfigEntries, "async_remove") as mock_remove:
        resp = await hassio_client.delete(
            f"/api/hassio_push/discovery/{uuid.hex}",
            json={"service": "mqtt", "uuid": uuid.hex},
        )
        await hass.async_block_till_done()

        expect(resp.status).to_equal(HTTPStatus.OK)
        get_discovery_message.assert_called_once_with(uuid)
        mock_remove.assert_not_called()
        expect("Retrieve wrong unload for mqtt" in caplog.text).to_equal(True)


@test
async def delete_hassio_discovery_non_admin(
    hass: HomeAssistant = Depends(hass_fixture),
    hassio_client: TestClient = Depends(hassio_client),
    _addon_installed: AsyncMock = Depends(addon_installed),
    _get_addon_discovery_info: AsyncMock = Depends(get_addon_discovery_info),
    get_discovery_message: AsyncMock = Depends(get_discovery_message),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test deleting a discovery item fails for non-admin users."""
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    entry = MockConfigEntry(
        domain=MQTT_DOMAIN,
        discovery_keys={
            "hassio": (DiscoveryKey(domain="hassio", key=TEST_UUID, version=1),)
        },
        unique_id=(uuid := uuid4()).hex,
        state=config_entries.ConfigEntryState.LOADED,
        source=config_entries.SOURCE_HASSIO,
    )
    entry.add_to_hass(hass)

    hass_admin_user.groups = []

    with patch.object(ConfigEntries, "async_remove") as mock_remove:
        resp = await hassio_client.delete(
            f"/api/hassio_push/discovery/{uuid.hex}",
            json={"service": "mqtt", "uuid": uuid.hex},
        )
        await hass.async_block_till_done()

        expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)
        get_discovery_message.assert_not_called()
        mock_remove.assert_not_called()


@test.cases(
    test.case(
        "matching_key_hassio",
        entry_domain="mock-domain",
        entry_discovery_keys={
            "hassio": (DiscoveryKey(domain="hassio", key=TEST_UUID, version=1),)
        },
        entry_source=config_entries.SOURCE_HASSIO,
    ),
    test.case(
        "matching_key_hassio_with_other",
        entry_domain="mock-domain",
        entry_discovery_keys={
            "hassio": (DiscoveryKey(domain="hassio", key=TEST_UUID, version=1),),
            "other": (DiscoveryKey(domain="other", key="blah", version=1),),
        },
        entry_source=config_entries.SOURCE_HASSIO,
    ),
    test.case(
        "matching_key_other_domain_hassio",
        entry_domain="comp",
        entry_discovery_keys={
            "hassio": (DiscoveryKey(domain="hassio", key=TEST_UUID, version=1),)
        },
        entry_source=config_entries.SOURCE_HASSIO,
    ),
    test.case(
        "matching_key_ignore",
        entry_domain="mock-domain",
        entry_discovery_keys={
            "hassio": (DiscoveryKey(domain="hassio", key=TEST_UUID, version=1),)
        },
        entry_source=config_entries.SOURCE_IGNORE,
    ),
    test.case(
        "matching_key_hassio_with_other_ignore",
        entry_domain="mock-domain",
        entry_discovery_keys={
            "hassio": (DiscoveryKey(domain="hassio", key=TEST_UUID, version=1),),
            "other": (DiscoveryKey(domain="other", key="blah", version=1),),
        },
        entry_source=config_entries.SOURCE_IGNORE,
    ),
    test.case(
        "matching_key_other_domain_ignore",
        entry_domain="comp",
        entry_discovery_keys={
            "hassio": (DiscoveryKey(domain="hassio", key=TEST_UUID, version=1),)
        },
        entry_source=config_entries.SOURCE_IGNORE,
    ),
    test.case(
        "matching_key_user",
        entry_domain="mock-domain",
        entry_discovery_keys={
            "hassio": (DiscoveryKey(domain="hassio", key=TEST_UUID, version=1),)
        },
        entry_source=config_entries.SOURCE_USER,
    ),
    test.case(
        "matching_key_hassio_with_other_user",
        entry_domain="mock-domain",
        entry_discovery_keys={
            "hassio": (DiscoveryKey(domain="hassio", key=TEST_UUID, version=1),),
            "other": (DiscoveryKey(domain="other", key="blah", version=1),),
        },
        entry_source=config_entries.SOURCE_USER,
    ),
    test.case(
        "matching_key_other_domain_user",
        entry_domain="comp",
        entry_discovery_keys={
            "hassio": (DiscoveryKey(domain="hassio", key=TEST_UUID, version=1),)
        },
        entry_source=config_entries.SOURCE_USER,
    ),
)
async def hassio_rediscover(
    entry_domain: str,
    entry_discovery_keys: dict[str, tuple[DiscoveryKey, ...]],
    entry_source: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _hassio_client: TestClient = Depends(hassio_client),
    _addon_installed: AsyncMock = Depends(addon_installed),
    _get_addon_discovery_info: AsyncMock = Depends(get_addon_discovery_info),
    get_discovery_message: AsyncMock = Depends(get_discovery_message),
) -> None:
    """Test we reinitiate flows when an ignored config entry is removed."""

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    entry = MockConfigEntry(
        domain=entry_domain,
        discovery_keys=entry_discovery_keys,
        unique_id="mock-unique-id",
        state=config_entries.ConfigEntryState.LOADED,
        source=entry_source,
    )
    entry.add_to_hass(hass)

    get_discovery_message.return_value = Discovery(
        addon="mosquitto",
        service="mqtt",
        uuid=(uuid := uuid4()),
        config={
            "broker": "mock-broker",
            "port": 1883,
            "username": "mock-user",
            "password": "mock-pass",
            "protocol": "3.1.1",
        },
    )

    expected_context = {
        "discovery_key": DiscoveryKey(domain="hassio", key=uuid.hex, version=1),
        "source": config_entries.SOURCE_HASSIO,
    }

    with patch.object(hass.config_entries.flow, "async_init") as mock_init:
        await hass.config_entries.async_remove(entry.entry_id)
        await hass.async_block_till_done()

        expect(len(mock_init.mock_calls)).to_equal(1)
        expect(mock_init.mock_calls[0][1][0]).to_equal("mqtt")
        expect(mock_init.mock_calls[0][2]["context"]).to_equal(expected_context)


@test.cases(
    test.case(
        "discovery_key_other_domain",
        entry_domain="mock-domain",
        entry_discovery_keys={
            "bluetooth": (DiscoveryKey(domain="bluetooth", key="test", version=1),)
        },
        entry_source=config_entries.SOURCE_IGNORE,
        entry_unique_id="mock-unique-id",
    ),
    test.case(
        "discovery_key_future_version",
        entry_domain="mock-domain",
        entry_discovery_keys={
            "hassio": (DiscoveryKey(domain="hassio", key="test", version=2),)
        },
        entry_source=config_entries.SOURCE_IGNORE,
        entry_unique_id="mock-unique-id",
    ),
)
async def hassio_rediscover_no_match(
    entry_domain: str,
    entry_discovery_keys: dict[str, tuple[DiscoveryKey, ...]],
    entry_source: str,
    entry_unique_id: str,
    hass: HomeAssistant = Depends(hass_fixture),
    hassio_client: TestClient = Depends(hassio_client),
) -> None:
    """Test we don't reinitiate flows when a non matching config entry is removed."""

    mock_integration(hass, MockModule(entry_domain))

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    entry = MockConfigEntry(
        domain=entry_domain,
        discovery_keys=entry_discovery_keys,
        unique_id=entry_unique_id,
        state=config_entries.ConfigEntryState.LOADED,
        source=entry_source,
    )
    entry.add_to_hass(hass)

    with patch.object(hass.config_entries.flow, "async_init") as mock_init:
        await hass.config_entries.async_remove(entry.entry_id)
        await hass.async_block_till_done()

        expect(len(mock_init.mock_calls)).to_equal(0)
