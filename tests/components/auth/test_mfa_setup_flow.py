"""Tests for the mfa setup flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.auth import auth_manager_from_config
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from tests.common import CLIENT_ID, MockUser, ensure_auth_manager_loaded
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fx,
)
from tests.typing import WebSocketGenerator


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def ws_setup_depose_mfa(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test set up mfa module for current user."""
    hass.auth = await auth_manager_from_config(
        hass,
        provider_configs=[
            {
                "type": "insecure_example",
                "users": [
                    {
                        "username": "test-user",
                        "password": "test-pass",
                        "name": "Test Name",
                    }
                ],
            }
        ],
        module_configs=[
            {
                "type": "insecure_example",
                "id": "example_module",
                "data": [{"user_id": "mock-user", "pin": "123456"}],
            }
        ],
    )
    ensure_auth_manager_loaded(hass.auth)
    await async_setup_component(hass, "auth", {"http": {}})

    user = MockUser(id="mock-user").add_to_hass(hass)
    cred = await hass.auth.auth_providers[0].async_get_or_create_credentials(
        {"username": "test-user"}
    )
    await hass.auth.async_link_user(user, cred)
    refresh_token = await hass.auth.async_create_refresh_token(user, CLIENT_ID)
    access_token = hass.auth.async_create_access_token(refresh_token)

    client = await hass_ws_client(hass, access_token)

    await client.send_json(
        {
            "id": 10,
            "type": "auth/setup_mfa",
            "mfa_module_id": "invalid_module",
        }
    )

    result = await client.receive_json()
    expect(result["id"]).to_equal(10)
    expect(result["success"]).to_equal(False)
    expect(result["error"]["code"]).to_equal("no_module")

    await client.send_json(
        {
            "id": 11,
            "type": "auth/setup_mfa",
            "mfa_module_id": "example_module",
        }
    )

    result = await client.receive_json()
    expect(result["id"]).to_equal(11)
    expect(result["success"]).to_equal(True)

    flow = result["result"]
    # Cannot use identity `is` check here as the value is parsed from JSON
    expect(flow["type"]).to_equal(FlowResultType.FORM.value)
    expect(flow["handler"]).to_equal("example_module")
    expect(flow["step_id"]).to_equal("init")
    expect(flow["data_schema"][0]).to_equal(
        {"type": "string", "name": "pin", "required": True}
    )

    await client.send_json(
        {
            "id": 12,
            "type": "auth/setup_mfa",
            "flow_id": flow["flow_id"],
            "user_input": {"pin": "654321"},
        }
    )

    result = await client.receive_json()
    expect(result["id"]).to_equal(12)
    expect(result["success"]).to_equal(True)

    flow = result["result"]
    # Cannot use identity `is` check here as the value is parsed from JSON
    expect(flow["type"]).to_equal(FlowResultType.CREATE_ENTRY.value)
    expect(flow["handler"]).to_equal("example_module")
    expect(flow["data"]["result"]).to_equal(None)

    await client.send_json(
        {
            "id": 13,
            "type": "auth/depose_mfa",
            "mfa_module_id": "invalid_id",
        }
    )

    result = await client.receive_json()
    expect(result["id"]).to_equal(13)
    expect(result["success"]).to_equal(False)
    expect(result["error"]["code"]).to_equal("disable_failed")

    await client.send_json(
        {
            "id": 14,
            "type": "auth/depose_mfa",
            "mfa_module_id": "example_module",
        }
    )

    result = await client.receive_json()
    expect(result["id"]).to_equal(14)
    expect(result["success"]).to_equal(True)
    expect(result["result"]).to_equal("done")
