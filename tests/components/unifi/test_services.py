"""UniFi service tests."""

from typing import Any
from unittest.mock import PropertyMock, patch

import aiounifi
from tryke import Depends, expect, fixture, test

from homeassistant.components.unifi.const import CONF_SITE_ID, DOMAIN
from homeassistant.components.unifi.services import (
    SERVICE_RECONNECT_CLIENT,
    SERVICE_REMOVE_CLIENTS,
)
from homeassistant.const import ATTR_DEVICE_ID, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import device_registry as dr

from ._fixtures import (
    _unifi_environment,
    setup_unifi_integration,
)

from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _env: tuple[HomeAssistant, AiohttpClientMocker] = Depends(_unifi_environment),
) -> int:
    """Anchor fixture for tryke Depends() resolution."""
    return 0


@test
async def reconnect_client(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Verify call to reconnect client is performed as expected."""
    client_payload: list[dict[str, Any]] = [
        {"is_wired": False, "mac": "00:00:00:00:00:01"}
    ]
    config_entry_setup = await setup_unifi_integration(
        hass, aioclient_mock, client_payload=client_payload
    )

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        f"https://{config_entry_setup.data[CONF_HOST]}:1234"
        f"/api/s/{config_entry_setup.data[CONF_SITE_ID]}/cmd/stamgr",
    )

    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_setup.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, client_payload[0]["mac"])},
    )

    await hass.services.async_call(
        DOMAIN,
        SERVICE_RECONNECT_CLIENT,
        service_data={ATTR_DEVICE_ID: device_entry.id},
        blocking=True,
    )
    expect(aioclient_mock.call_count).to_equal(1)


@test
async def reconnect_non_existent_device(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Verify ServiceValidationError is raised if device does not exist."""
    await setup_unifi_integration(hass, aioclient_mock)
    aioclient_mock.clear_requests()

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RECONNECT_CLIENT,
            service_data={ATTR_DEVICE_ID: "device_entry.id"},
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised).not_.to_be(None)
    expect(raised.translation_domain).to_equal(DOMAIN)
    expect(raised.translation_key).to_equal("reconnect_client_device_not_found")
    expect(aioclient_mock.call_count).to_equal(0)


@test
async def reconnect_device_without_mac(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Verify ServiceValidationError is raised if device does not have a known mac."""
    config_entry_setup = await setup_unifi_integration(hass, aioclient_mock)
    aioclient_mock.clear_requests()

    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_setup.entry_id,
        connections={("other connection", "not mac")},
    )

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RECONNECT_CLIENT,
            service_data={ATTR_DEVICE_ID: device_entry.id},
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised).not_.to_be(None)
    expect(raised.translation_domain).to_equal(DOMAIN)
    expect(raised.translation_key).to_equal("reconnect_client_no_mac")
    expect(aioclient_mock.call_count).to_equal(0)


@test
async def reconnect_client_hub_unavailable(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Verify no call is made if hub is unavailable."""
    client_payload: list[dict[str, Any]] = [
        {"is_wired": False, "mac": "00:00:00:00:00:01"}
    ]
    config_entry_setup = await setup_unifi_integration(
        hass, aioclient_mock, client_payload=client_payload
    )

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        f"https://{config_entry_setup.data[CONF_HOST]}:1234"
        f"/api/s/{config_entry_setup.data[CONF_SITE_ID]}/cmd/stamgr",
    )

    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_setup.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, client_payload[0]["mac"])},
    )

    with patch(
        "homeassistant.components.unifi.UnifiHub.available", new_callable=PropertyMock
    ) as ws_mock:
        ws_mock.return_value = False
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RECONNECT_CLIENT,
            service_data={ATTR_DEVICE_ID: device_entry.id},
            blocking=True,
        )
    expect(aioclient_mock.call_count).to_equal(0)


@test
async def reconnect_client_unknown_mac(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Verify no call is made if trying to reconnect a mac unknown to hub."""
    config_entry_setup = await setup_unifi_integration(hass, aioclient_mock)
    aioclient_mock.clear_requests()
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_setup.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "mac unknown to hub")},
    )

    await hass.services.async_call(
        DOMAIN,
        SERVICE_RECONNECT_CLIENT,
        service_data={ATTR_DEVICE_ID: device_entry.id},
        blocking=True,
    )
    expect(aioclient_mock.call_count).to_equal(0)


@test
async def reconnect_wired_client(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Verify no call is made if client is wired."""
    client_payload: list[dict[str, Any]] = [
        {"is_wired": True, "mac": "00:00:00:00:00:01"}
    ]
    config_entry_setup = await setup_unifi_integration(
        hass, aioclient_mock, client_payload=client_payload
    )
    aioclient_mock.clear_requests()
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_setup.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, client_payload[0]["mac"])},
    )

    await hass.services.async_call(
        DOMAIN,
        SERVICE_RECONNECT_CLIENT,
        service_data={ATTR_DEVICE_ID: device_entry.id},
        blocking=True,
    )
    expect(aioclient_mock.call_count).to_equal(0)


@test
async def remove_clients(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Verify removing different variations of clients work."""
    clients_all_payload: list[dict[str, Any]] = [
        {"mac": "00:00:00:00:00:00"},
        {"first_seen": 100, "last_seen": 500, "mac": "00:00:00:00:00:01"},
        {"first_seen": 100, "last_seen": 1100, "mac": "00:00:00:00:00:02"},
        {
            "first_seen": 100,
            "last_seen": 500,
            "fixed_ip": "1.2.3.4",
            "mac": "00:00:00:00:00:03",
        },
        {
            "first_seen": 100,
            "last_seen": 500,
            "hostname": "hostname",
            "mac": "00:00:00:00:00:04",
        },
        {
            "first_seen": 100,
            "last_seen": 500,
            "name": "name",
            "mac": "00:00:00:00:00:05",
        },
    ]
    config_entry_setup = await setup_unifi_integration(
        hass, aioclient_mock, clients_all_payload=clients_all_payload
    )

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        f"https://{config_entry_setup.data[CONF_HOST]}:1234"
        f"/api/s/{config_entry_setup.data[CONF_SITE_ID]}/cmd/stamgr",
    )

    await hass.services.async_call(DOMAIN, SERVICE_REMOVE_CLIENTS, blocking=True)
    expect(aioclient_mock.mock_calls[0][2]).to_equal(
        {
            "cmd": "forget-sta",
            "macs": ["00:00:00:00:00:00", "00:00:00:00:00:01"],
        }
    )

    expect(
        await hass.config_entries.async_unload(config_entry_setup.entry_id)
    ).to_be(True)


@test
async def remove_clients_hub_unavailable(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Verify no call is made if UniFi Network is unavailable."""
    clients_all_payload: list[dict[str, Any]] = [
        {"first_seen": 100, "last_seen": 500, "mac": "00:00:00:00:00:01"}
    ]
    await setup_unifi_integration(
        hass, aioclient_mock, clients_all_payload=clients_all_payload
    )

    aioclient_mock.clear_requests()
    with patch(
        "homeassistant.components.unifi.UnifiHub.available", new_callable=PropertyMock
    ) as ws_mock:
        ws_mock.return_value = False
        await hass.services.async_call(DOMAIN, SERVICE_REMOVE_CLIENTS, blocking=True)
    expect(aioclient_mock.call_count).to_equal(0)


@test
async def remove_clients_no_call_on_empty_list(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Verify no call is made if no fitting client has been added to the list."""
    clients_all_payload: list[dict[str, Any]] = [
        {"first_seen": 100, "last_seen": 1100, "mac": "00:00:00:00:00:01"}
    ]
    await setup_unifi_integration(
        hass, aioclient_mock, clients_all_payload=clients_all_payload
    )

    aioclient_mock.clear_requests()
    await hass.services.async_call(DOMAIN, SERVICE_REMOVE_CLIENTS, blocking=True)
    expect(aioclient_mock.call_count).to_equal(0)


@test
async def services_handle_unloaded_config_entry(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Verify no call is made if config entry is unloaded."""
    clients_all_payload: list[dict[str, Any]] = [
        {"first_seen": 100, "last_seen": 500, "mac": "00:00:00:00:00:01"}
    ]
    config_entry_setup = await setup_unifi_integration(
        hass, aioclient_mock, clients_all_payload=clients_all_payload
    )

    await hass.config_entries.async_unload(config_entry_setup.entry_id)
    await hass.async_block_till_done()

    aioclient_mock.clear_requests()

    await hass.services.async_call(DOMAIN, SERVICE_REMOVE_CLIENTS, blocking=True)
    expect(aioclient_mock.call_count).to_equal(0)


@test
async def reconnect_client_request_failed(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Verify HomeAssistantError is raised when API request fails."""
    client_payload: list[dict[str, Any]] = [
        {"is_wired": False, "mac": "00:00:00:00:00:01"}
    ]
    config_entry_setup = await setup_unifi_integration(
        hass, aioclient_mock, client_payload=client_payload
    )

    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_setup.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, client_payload[0]["mac"])},
    )

    raised: HomeAssistantError | None = None
    with patch.object(
        config_entry_setup.runtime_data.api,
        "request",
        side_effect=aiounifi.AiounifiException,
    ):
        try:
            await hass.services.async_call(
                DOMAIN,
                SERVICE_RECONNECT_CLIENT,
                service_data={ATTR_DEVICE_ID: device_entry.id},
                blocking=True,
            )
        except HomeAssistantError as exc:
            raised = exc

    expect(raised).not_.to_be(None)
    expect(raised.translation_domain).to_equal(DOMAIN)
    expect(raised.translation_key).to_equal("reconnect_client_request_failed")


@test
async def remove_clients_request_failed(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Verify HomeAssistantError is raised when API request fails."""
    clients_all_payload: list[dict[str, Any]] = [
        {"first_seen": 100, "last_seen": 500, "mac": "00:00:00:00:00:01"}
    ]
    config_entry_setup = await setup_unifi_integration(
        hass, aioclient_mock, clients_all_payload=clients_all_payload
    )

    raised: HomeAssistantError | None = None
    with patch.object(
        config_entry_setup.runtime_data.api,
        "request",
        side_effect=aiounifi.AiounifiException,
    ):
        try:
            await hass.services.async_call(
                DOMAIN, SERVICE_REMOVE_CLIENTS, blocking=True
            )
        except HomeAssistantError as exc:
            raised = exc

    expect(raised).not_.to_be(None)
    expect(raised.translation_domain).to_equal(DOMAIN)
    expect(raised.translation_key).to_equal("remove_clients_request_failed")
