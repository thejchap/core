"""Tests for ESPHome websocket API."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.esphome.const import CONF_NOISE_PSK
from homeassistant.components.esphome.websocket_api import ENTRY_ID, TYPE
from homeassistant.core import HomeAssistant

from ._fixtures import init_integration

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, hass_ws_client
from tests.typing import WebSocketGenerator


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(init_integration),
) -> MockConfigEntry:
    """Anchor cross-module fixtures so tryke resolves before the test body."""
    return entry


@test
async def get_encryption_key(
    init_integration: MockConfigEntry = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client),
) -> None:
    """Test get encryption key."""
    mock_config_entry = init_integration

    websocket_client = await hass_ws_client()
    await websocket_client.send_json_auto_id(
        {
            TYPE: "esphome/get_encryption_key",
            ENTRY_ID: mock_config_entry.entry_id,
        }
    )

    response = await websocket_client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal(
        {"encryption_key": mock_config_entry.data.get(CONF_NOISE_PSK)}
    )
