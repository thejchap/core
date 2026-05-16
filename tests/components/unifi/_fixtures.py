"""Tryke fixtures for the UniFi Network integration."""

from collections.abc import AsyncGenerator, Callable, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture

from homeassistant.components.unifi import STORAGE_KEY, STORAGE_VERSION
from homeassistant.components.unifi.const import CONF_SITE_ID, DOMAIN
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    CONTENT_TYPE_JSON,
)
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
)
from tests.test_util.aiohttp import AiohttpClientMocker

DEFAULT_CONFIG_ENTRY_ID = "1"
DEFAULT_HOST = "1.2.3.4"
DEFAULT_PORT = 1234
DEFAULT_SITE = "site_id"

DEFAULT_SITE_PAYLOAD: list[dict[str, Any]] = [
    {"desc": "Site name", "name": "site_id", "role": "admin", "_id": "1"}
]

DEFAULT_SYSTEM_INFORMATION_PAYLOAD: list[dict[str, Any]] = [
    {
        "anonymous_controller_id": "24f81231-a456-4c32-abcd-f5612345385f",
        "build": "atag_7.4.162_21057",
        "console_display_version": "3.1.15",
        "hostname": "UDMP",
        "name": "UDMP",
        "previous_version": "7.4.156",
        "timezone": "Europe/Stockholm",
        "ubnt_device_type": "UDMPRO",
        "udm_version": "3.0.20.9281",
        "update_available": False,
        "update_downloaded": False,
        "uptime": 1196290,
        "version": "7.4.162",
    }
]


def default_config_entry_data() -> dict[str, Any]:
    """Return the default config entry data for tests."""
    return {
        CONF_HOST: DEFAULT_HOST,
        CONF_USERNAME: "username",
        CONF_PASSWORD: "password",
        CONF_PORT: DEFAULT_PORT,
        CONF_SITE_ID: DEFAULT_SITE,
        CONF_VERIFY_SSL: False,
    }


@fixture
def mock_discovery() -> Generator[MagicMock]:
    """No real network traffic allowed."""
    with (
        patch(
            "homeassistant.components.unifi.config_flow._async_discover_unifi",
            return_value=None,
        ) as mock,
        patch(
            "homeassistant.components.unifi_discovery.discovery.AIOUnifiScanner",
            return_value=MagicMock(
                async_scan=AsyncMock(return_value=[]), found_devices=[]
            ),
        ),
    ):
        yield mock


@fixture
def mock_wireless_client_storage(
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Mock the known wireless storage."""
    hass_storage[STORAGE_KEY] = {"version": STORAGE_VERSION, "data": {}}


@fixture
def _mock_websocket() -> Generator[AsyncMock]:
    """Mock aiounifi websocket context manager."""
    with patch("aiounifi.controller.Connectivity.websocket") as ws_mock:
        # Default side_effect: block forever until cancelled.
        async def _wait_forever(*args: Any, **kwargs: Any) -> None:
            import asyncio  # noqa: PLC0415

            await asyncio.Event().wait()

        ws_mock.side_effect = _wait_forever
        yield ws_mock


def _register_unifi_mock_requests(
    aioclient_mock: AiohttpClientMocker,
    *,
    host: str = DEFAULT_HOST,
    site_id: str = DEFAULT_SITE,
    client_payload: list[dict[str, Any]] | None = None,
    clients_all_payload: list[dict[str, Any]] | None = None,
    device_payload: list[dict[str, Any]] | None = None,
    dpi_app_payload: list[dict[str, Any]] | None = None,
    dpi_group_payload: list[dict[str, Any]] | None = None,
    firewall_policy_payload: list[dict[str, Any]] | None = None,
    port_forward_payload: list[dict[str, Any]] | None = None,
    traffic_rule_payload: list[dict[str, Any]] | None = None,
    traffic_route_payload: list[dict[str, Any]] | None = None,
    site_payload: list[dict[str, Any]] | None = None,
    system_information_payload: list[dict[str, Any]] | None = None,
    wlan_payload: list[dict[str, Any]] | None = None,
) -> None:
    """Register default UniFi REST endpoint responses against aioclient_mock."""
    client_payload = client_payload if client_payload is not None else []
    clients_all_payload = clients_all_payload if clients_all_payload is not None else []
    device_payload = device_payload if device_payload is not None else []
    dpi_app_payload = dpi_app_payload if dpi_app_payload is not None else []
    dpi_group_payload = dpi_group_payload if dpi_group_payload is not None else []
    firewall_policy_payload = (
        firewall_policy_payload if firewall_policy_payload is not None else []
    )
    port_forward_payload = (
        port_forward_payload if port_forward_payload is not None else []
    )
    traffic_rule_payload = (
        traffic_rule_payload if traffic_rule_payload is not None else []
    )
    traffic_route_payload = (
        traffic_route_payload if traffic_route_payload is not None else []
    )
    site_payload = site_payload if site_payload is not None else DEFAULT_SITE_PAYLOAD
    system_information_payload = (
        system_information_payload
        if system_information_payload is not None
        else DEFAULT_SYSTEM_INFORMATION_PAYLOAD
    )
    wlan_payload = wlan_payload if wlan_payload is not None else []

    url = f"https://{host}:{DEFAULT_PORT}"

    def mock_get_request(path: str, payload: list[dict[str, Any]]) -> None:
        if path.startswith("/v2"):
            json = payload
        else:
            json = {"meta": {"rc": "OK"}, "data": payload}
        aioclient_mock.get(
            f"{url}{path}",
            json=json,
            headers={"content-type": CONTENT_TYPE_JSON},
        )

    aioclient_mock.get(url, status=302)
    aioclient_mock.post(
        f"{url}/api/login",
        json={"data": "login successful", "meta": {"rc": "ok"}},
        headers={"content-type": CONTENT_TYPE_JSON},
    )
    mock_get_request("/api/self/sites", site_payload)
    mock_get_request(f"/api/s/{site_id}/stat/sta", client_payload)
    mock_get_request(f"/api/s/{site_id}/rest/user", clients_all_payload)
    mock_get_request(f"/api/s/{site_id}/stat/device", device_payload)
    mock_get_request(f"/api/s/{site_id}/rest/dpiapp", dpi_app_payload)
    mock_get_request(f"/api/s/{site_id}/rest/dpigroup", dpi_group_payload)
    mock_get_request(
        f"/v2/api/site/{site_id}/firewall-policies", firewall_policy_payload
    )
    mock_get_request(f"/api/s/{site_id}/rest/portforward", port_forward_payload)
    mock_get_request(f"/api/s/{site_id}/stat/sysinfo", system_information_payload)
    mock_get_request(f"/api/s/{site_id}/rest/wlanconf", wlan_payload)
    mock_get_request(f"/v2/api/site/{site_id}/trafficrules", traffic_rule_payload)
    mock_get_request(f"/v2/api/site/{site_id}/trafficroutes", traffic_route_payload)


async def setup_unifi_integration(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    *,
    client_payload: list[dict[str, Any]] | None = None,
    clients_all_payload: list[dict[str, Any]] | None = None,
    device_payload: list[dict[str, Any]] | None = None,
) -> MockConfigEntry:
    """Set up the UniFi integration and return the MockConfigEntry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id=DEFAULT_CONFIG_ENTRY_ID,
        unique_id="1",
        data=default_config_entry_data(),
        options={},
    )
    config_entry.add_to_hass(hass)

    _register_unifi_mock_requests(
        aioclient_mock,
        host=DEFAULT_HOST,
        site_id=DEFAULT_SITE,
        client_payload=client_payload,
        clients_all_payload=clients_all_payload,
        device_payload=device_payload,
    )

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry


# Type alias for the setup callable below
type SetupUnifiFn = Callable[..., Any]


@fixture
async def _unifi_environment(
    _discovery: MagicMock = Depends(mock_discovery),
    _wireless_storage: None = Depends(mock_wireless_client_storage),
    _ws: AsyncMock = Depends(_mock_websocket),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> AsyncGenerator[tuple[HomeAssistant, AiohttpClientMocker]]:
    """Aggregate UniFi-side autouse fixtures into a single Depends target."""
    yield hass, aioclient_mock
