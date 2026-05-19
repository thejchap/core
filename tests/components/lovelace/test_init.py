"""Test the Lovelace initialization."""

from typing import Any
from unittest.mock import MagicMock

import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant.components.lovelace import _validate_url_slug
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import (
    mock_add_onboarding_listener as mock_add_onboarding_listener_fx,
    mock_onboarding_done as mock_onboarding_done_fx,
    mock_onboarding_not_done as mock_onboarding_not_done_fx,
)

from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
    hass_ws_client as hass_ws_client_fx,
)
from tests.typing import WebSocketGenerator


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def create_dashboards_when_onboarded(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    mock_onboarding_done: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test we don't create dashboards when onboarded."""
    client = await hass_ws_client(hass)

    expect(await async_setup_component(hass, "lovelace", {})).to_be(True)

    await client.send_json_auto_id({"type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal([])


@test
async def create_dashboards_when_not_onboarded(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    mock_add_onboarding_listener: MagicMock = Depends(mock_add_onboarding_listener_fx),
    mock_onboarding_not_done: MagicMock = Depends(mock_onboarding_not_done_fx),
) -> None:
    """Test we automatically create dashboards when not onboarded."""
    client = await hass_ws_client(hass)

    expect(await async_setup_component(hass, "lovelace", {})).to_be(True)

    # Call onboarding listener
    mock_add_onboarding_listener.mock_calls[0][1][1]()
    await hass.async_block_till_done()

    await client.send_json_auto_id({"type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal(
        [
            {
                "icon": "mdi:map",
                "id": "map",
                "mode": "storage",
                "require_admin": False,
                "show_in_sidebar": True,
                "title": "Map",
                "url_path": "map",
            }
        ]
    )

    await client.send_json_auto_id({"type": "lovelace/config", "url_path": "map"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal({"strategy": {"type": "map"}})


@test.cases(
    test.case("lovelace", value="lovelace", expected="lovelace"),
    test.case("my-dashboard", value="my-dashboard", expected="my-dashboard"),
    test.case(
        "my-cool-dashboard", value="my-cool-dashboard", expected="my-cool-dashboard"
    ),
)
def validate_url_slug_valid(value: str, expected: str) -> None:
    """Test _validate_url_slug with valid values."""
    expect(_validate_url_slug(value)).to_equal(expected)


@test.cases(
    test.case("none", value=None, error_message=r"Slug should not be None"),
    test.case(
        "no_dash",
        value="nodash",
        error_message=r"Url path needs to contain a hyphen \(-\)",
    ),
    test.case(
        "invalid_chars",
        value="my-dash board",
        error_message=r"invalid slug my-dash board \(try my-dash-board\)",
    ),
)
def validate_url_slug_invalid(value: Any, error_message: str) -> None:
    """Test _validate_url_slug with invalid values."""
    expect(lambda: _validate_url_slug(value)).to_raise(vol.Invalid, match=error_message)
