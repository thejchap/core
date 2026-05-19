"""Tests for the system health component init."""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from aiohttp.client_exceptions import ClientError
from tryke import Depends, expect, fixture, test

from homeassistant.components import system_health
from homeassistant.components.system_health import async_register_info
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import get_system_health_info, mock_platform
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fx,
    hass as hass_fx,
    hass_ws_client as hass_ws_client_fx,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


async def gather_system_health_info(
    hass: HomeAssistant, hass_ws_client: Any
) -> dict[str, Any]:
    """Gather all info."""
    client = await hass_ws_client(hass)

    resp = await client.send_json({"id": 6, "type": "system_health/info"})

    resp = await client.receive_json()
    assert resp["success"]

    data: dict[str, Any] = {}

    resp = await client.receive_json()
    assert resp["event"]["type"] == "initial"
    data = resp["event"]["data"]

    while True:
        resp = await client.receive_json()
        event = resp["event"]

        if event["type"] == "finish":
            break

        assert event["type"] == "update"

        if event["success"]:
            data[event["domain"]]["info"][event["key"]] = event["data"]
        else:
            data[event["domain"]]["info"][event["key"]] = event["error"]

    return data


@test
async def info_endpoint_return_info(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: Any = Depends(hass_ws_client_fx),
) -> None:
    """Test that the info endpoint works."""
    expect(await async_setup_component(hass, "homeassistant", {})).to_be_truthy()

    with patch(
        "homeassistant.components.homeassistant.system_health.system_health_info",
        return_value={"hello": True},
    ):
        expect(await async_setup_component(hass, "system_health", {})).to_be_truthy()

    data = await gather_system_health_info(hass, hass_ws_client)

    expect(len(data)).to_equal(1)
    data = data["homeassistant"]
    expect(data).to_equal({"info": {"hello": True}})


@test
async def info_endpoint_register_callback(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: Any = Depends(hass_ws_client_fx),
) -> None:
    """Test that the info endpoint allows registering callbacks."""

    async def mock_info(hass: HomeAssistant) -> dict[str, Any]:
        return {"storage": "YAML"}

    async_register_info(hass, "lovelace", mock_info)
    expect(await async_setup_component(hass, "system_health", {})).to_be_truthy()
    data = await gather_system_health_info(hass, hass_ws_client)

    expect(len(data)).to_equal(1)
    data = data["lovelace"]
    expect(data).to_equal({"info": {"storage": "YAML"}})

    expect(await get_system_health_info(hass, "lovelace")).to_equal({"storage": "YAML"})


@test
async def info_endpoint_register_callback_timeout(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: Any = Depends(hass_ws_client_fx),
) -> None:
    """Test that the info endpoint timing out."""

    async def mock_info(hass: HomeAssistant) -> dict[str, Any]:
        raise TimeoutError

    async_register_info(hass, "lovelace", mock_info)
    expect(await async_setup_component(hass, "system_health", {})).to_be_truthy()
    data = await gather_system_health_info(hass, hass_ws_client)

    expect(len(data)).to_equal(1)
    data = data["lovelace"]
    expect(data).to_equal({"info": {"error": {"type": "failed", "error": "timeout"}}})


@test
async def info_endpoint_register_callback_exc(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: Any = Depends(hass_ws_client_fx),
) -> None:
    """Test that the info endpoint requires auth."""

    async def mock_info(hass: HomeAssistant) -> dict[str, Any]:
        raise Exception("TEST ERROR")  # noqa: TRY002

    async_register_info(hass, "lovelace", mock_info)
    expect(await async_setup_component(hass, "system_health", {})).to_be_truthy()
    data = await gather_system_health_info(hass, hass_ws_client)

    expect(len(data)).to_equal(1)
    data = data["lovelace"]
    expect(data).to_equal({"info": {"error": {"type": "failed", "error": "unknown"}}})


@test
async def platform_loading(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: Any = Depends(hass_ws_client_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test registering via platform."""
    aioclient_mock.get("http://example.com/status", text="")
    aioclient_mock.get("http://example.com/status_fail", exc=ClientError)
    aioclient_mock.get("http://example.com/timeout", exc=TimeoutError)
    hass.config.components.add("fake_integration")
    mock_platform(
        hass,
        "fake_integration.system_health",
        Mock(
            async_register=lambda hass, register: register.async_register_info(
                AsyncMock(
                    return_value={
                        "hello": "info",
                        "server_reachable": system_health.async_check_can_reach_url(
                            hass, "http://example.com/status"
                        ),
                        "server_fail_reachable": system_health.async_check_can_reach_url(
                            hass,
                            "http://example.com/status_fail",
                            more_info="http://more-info-url.com",
                        ),
                        "server_timeout": system_health.async_check_can_reach_url(
                            hass,
                            "http://example.com/timeout",
                            more_info="http://more-info-url.com",
                        ),
                        "async_crash": AsyncMock(side_effect=ValueError)(),
                    }
                ),
                "/config/fake_integration",
            )
        ),
    )

    expect(await async_setup_component(hass, "system_health", {})).to_be_truthy()
    data = await gather_system_health_info(hass, hass_ws_client)

    expect(data["fake_integration"]).to_equal(
        {
            "info": {
                "hello": "info",
                "server_reachable": "ok",
                "server_fail_reachable": {
                    "type": "failed",
                    "error": "unreachable",
                    "more_info": "http://more-info-url.com",
                },
                "server_timeout": {
                    "type": "failed",
                    "error": "timeout",
                    "more_info": "http://more-info-url.com",
                },
                "async_crash": {
                    "type": "failed",
                    "error": "unknown",
                },
            },
            "manage_url": "/config/fake_integration",
        }
    )
