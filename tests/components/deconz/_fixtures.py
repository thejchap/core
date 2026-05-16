"""Tryke fixtures for deCONZ integration tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable, Generator
from typing import Any
from unittest.mock import patch

from pydeconz.websocket import Signal
from tryke import Depends, fixture

from homeassistant.components.deconz.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT, CONTENT_TYPE_JSON
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import aioclient_mock, hass as hass_fixture
from tests.test_util.aiohttp import AiohttpClientMocker

API_KEY = "1234567890ABCDEF"
BRIDGE_ID = "01234E56789A"
HOST = "1.2.3.4"
PORT = 80


def default_config_payload() -> dict[str, Any]:
    """Return default deCONZ /config payload."""
    return {
        "bridgeid": BRIDGE_ID,
        "ipaddress": HOST,
        "mac": "00:11:22:33:44:55",
        "modelid": "deCONZ",
        "name": "deCONZ mock gateway",
        "sw_version": "2.05.69",
        "uuid": "1234",
        "websocketport": 1234,
    }


def build_config_entry(
    *,
    options: dict[str, Any] | None = None,
    source: str = SOURCE_USER,
) -> MockConfigEntry:
    """Construct a deCONZ config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        entry_id="1",
        unique_id=BRIDGE_ID,
        data={
            CONF_API_KEY: API_KEY,
            CONF_HOST: HOST,
            CONF_PORT: PORT,
        },
        options=options or {},
        source=source,
    )


def register_get_request(
    aioclient: AiohttpClientMocker,
    *,
    deconz_payload: dict[str, Any] | None = None,
    config_payload: dict[str, Any] | None = None,
    alarm_system_payload: dict[str, Any] | None = None,
    group_payload: dict[str, Any] | None = None,
    light_payload: dict[str, Any] | None = None,
    sensor_payload: dict[str, Any] | None = None,
    host: str = HOST,
) -> dict[str, Any]:
    """Register the GET-/api/<key> mock and return the assembled payload.

    Mirrors the legacy ``mock_requests`` conftest fixture: builds the full
    deCONZ "everything" payload from the per-resource payloads, wraps single
    light/sensor payloads as the ``"0"`` entry, and registers a GET mock so
    the integration can fetch it during setup or refresh.
    """
    config_payload = config_payload if config_payload is not None else default_config_payload()
    alarm_system_payload = alarm_system_payload if alarm_system_payload is not None else {}
    group_payload = group_payload if group_payload is not None else {}
    light_payload = light_payload if light_payload is not None else {}
    sensor_payload = sensor_payload if sensor_payload is not None else {}

    data = dict(deconz_payload) if deconz_payload else {}
    data.setdefault("alarmsystems", alarm_system_payload)
    data.setdefault("config", config_payload)
    data.setdefault("groups", group_payload)
    if "state" in light_payload:
        light_payload = {"0": light_payload}
    data.setdefault("lights", light_payload)
    if "state" in sensor_payload or "config" in sensor_payload:
        sensor_payload = {"0": sensor_payload}
    data.setdefault("sensors", sensor_payload)

    url = f"http://{host}:{PORT}/api/{API_KEY}"
    aioclient.get(
        url,
        json=data,
        headers={"content-type": CONTENT_TYPE_JSON},
    )
    return data


async def setup_deconz(
    hass: HomeAssistant,
    aioclient: AiohttpClientMocker,
    *,
    options: dict[str, Any] | None = None,
    deconz_payload: dict[str, Any] | None = None,
    light_payload: dict[str, Any] | None = None,
    sensor_payload: dict[str, Any] | None = None,
    group_payload: dict[str, Any] | None = None,
) -> MockConfigEntry:
    """Set up the deCONZ integration with the requested payloads."""
    entry = build_config_entry(options=options)
    entry.add_to_hass(hass)
    register_get_request(
        aioclient,
        deconz_payload=deconz_payload,
        light_payload=light_payload,
        sensor_payload=sensor_payload,
        group_payload=group_payload,
    )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@fixture
def mock_websocket() -> Generator[Any]:
    """Patch pydeconz's WSClient so tests never open a real websocket."""
    with patch("pydeconz.gateway.WSClient") as mock:
        async def make_websocket_call(
            data: dict[str, Any] | None = None, state: str = ""
        ) -> None:
            pydeconz_gateway_session_handler = mock.call_args[0][3]
            signal: Signal
            if data:
                mock.return_value.data = data
                signal = Signal.DATA
            elif state:
                mock.return_value.state = state
                signal = Signal.CONNECTION_STATE
            await pydeconz_gateway_session_handler(signal)

        yield make_websocket_call


@fixture
def mock_put_request(
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> Callable[[str, str], AiohttpClientMocker]:
    """Return a callable that registers a PUT mock for a deCONZ path."""

    def __mock_requests(path: str, host: str = "") -> AiohttpClientMocker:
        url = f"http://{host or HOST}:{PORT}/api/{API_KEY}{path}"
        aioclient.put(url, json={}, headers={"content-type": CONTENT_TYPE_JSON})
        return aioclient

    return __mock_requests
