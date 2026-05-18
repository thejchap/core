"""Test deCONZ diagnostics (tryke port)."""

from __future__ import annotations

from typing import Any

from pydeconz.websocket import State
from tryke import Depends, expect, fixture, test

from homeassistant.components.deconz.diagnostics import (
    REDACT_CONFIG,
    REDACT_DECONZ_CONFIG,
)
from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from tests.components.deconz._fixtures import (
    default_config_payload,
    mock_websocket,
    setup_deconz,
)
from tests.components.diagnostics import get_diagnostics_for_config_entry
from tests.hass_fixtures import (
    ClientSessionGenerator,
    aioclient_mock,
    hass as hass_fixture,
    hass_client as hass_client_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor fixture for tryke fixture-injection."""
    return 0


@test
async def entry_diagnostics(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    websocket: Any = Depends(mock_websocket),
) -> None:
    """Test config entry diagnostics."""
    config_entry_setup = await setup_deconz(hass, aioclient)

    await websocket(state=State.RUNNING)
    await hass.async_block_till_done()

    result = await get_diagnostics_for_config_entry(
        hass, hass_client, config_entry_setup
    )

    expected_entry = async_redact_data(config_entry_setup.as_dict(), REDACT_CONFIG)
    expected_deconz_config = async_redact_data(
        default_config_payload(), REDACT_DECONZ_CONFIG
    )

    # Drop keys that vary across runs (timestamps)
    result_config = {
        k: v for k, v in result["config"].items() if k not in ("created_at", "modified_at")
    }
    expected_entry_filtered = {
        k: v
        for k, v in expected_entry.items()
        if k not in ("created_at", "modified_at")
    }

    expect(result_config).to_equal(expected_entry_filtered)
    expect(result["deconz_config"]).to_equal(expected_deconz_config)
    expect(result["websocket_state"]).to_equal("running")
    expect(result["deconz_ids"]).to_equal({})
    expect(result["events"]).to_equal({})
    expect(result["alarm_systems"]).to_equal({})
    expect(result["groups"]).to_equal({})
    expect(result["lights"]).to_equal({})
    expect(result["scenes"]).to_equal({})
    expect(result["sensors"]).to_equal({})
    expect(result["entities"]).to_equal(
        {
            "alarm_control_panel": [],
            "binary_sensor": [],
            "button": [],
            "climate": [],
            "cover": [],
            "fan": [],
            "light": [],
            "lock": [],
            "number": [],
            "scene": [],
            "select": [],
            "sensor": [],
            "siren": [],
            "switch": [],
        }
    )
