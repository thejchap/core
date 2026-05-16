"""Tests for Logger Websocket API commands."""

import logging
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries, loader
from homeassistant.components.logger.helpers import DATA_LOGGER
from homeassistant.components.websocket_api import TYPE_RESULT
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import _trigger_executor

from tests.common import (
    MockModule,
    mock_config_flow,
    mock_integration,
    mock_platform,
)
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fixture,
    hass_read_only_access_token as hass_read_only_access_token_fixture,
    hass_ws_client as hass_ws_client_fixture,
)


@fixture
def _setup_trigger(_t: int = Depends(_trigger_executor)) -> int:
    """Ensure _trigger_executor fixture is resolved (anchored to module)."""
    return _t


@test
async def integration_log_info(
    _executor: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    hass_admin_user=Depends(hass_admin_user_fixture),
) -> None:
    """Test fetching integration log info."""

    expect(await async_setup_component(hass, "logger", {})).to_be_truthy()

    logging.getLogger("homeassistant.components.http").setLevel(logging.DEBUG)
    logging.getLogger("homeassistant.components.websocket_api").setLevel(logging.DEBUG)

    websocket_client = await hass_ws_client()
    await websocket_client.send_json({"id": 7, "type": "logger/log_info"})

    msg = await websocket_client.receive_json()
    expect(msg["id"]).to_equal(7)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    expect({"domain": "http", "level": logging.DEBUG} in msg["result"]).to_be_truthy()


@test
async def integration_log_info_discovered_flows(
    _executor: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    hass_admin_user=Depends(hass_admin_user_fixture),
) -> None:
    """Test that log info includes discovered flows."""
    expect(await async_setup_component(hass, "logger", {})).to_be_truthy()

    # Set up a discovery flow (zeroconf)
    mock_integration(hass, MockModule("discovered_integration"))
    mock_platform(hass, "discovered_integration.config_flow", None)

    class DiscoveryFlow(config_entries.ConfigFlow, domain="discovered_integration"):
        """Test discovery flow."""

        VERSION = 1

        async def async_step_zeroconf(self, discovery_info=None):
            """Test zeroconf step."""
            return self.async_show_form(step_id="zeroconf")

    # Set up a user flow (non-discovery)
    mock_integration(hass, MockModule("user_flow_integration"))
    mock_platform(hass, "user_flow_integration.config_flow", None)

    class UserFlow(config_entries.ConfigFlow, domain="user_flow_integration"):
        """Test user flow."""

        VERSION = 1

        async def async_step_user(self, user_input=None):
            """Test user step."""
            return self.async_show_form(step_id="user")

    with (
        mock_config_flow("discovered_integration", DiscoveryFlow),
        mock_config_flow("user_flow_integration", UserFlow),
    ):
        await hass.config_entries.flow.async_init(
            "discovered_integration",
            context={"source": config_entries.SOURCE_ZEROCONF},
        )
        await hass.config_entries.flow.async_init(
            "user_flow_integration",
            context={"source": config_entries.SOURCE_USER},
        )

        flows = hass.config_entries.flow.async_progress()
        expect(len(flows)).to_equal(2)

        websocket_client = await hass_ws_client()
        await websocket_client.send_json({"id": 7, "type": "logger/log_info"})

        msg = await websocket_client.receive_json()
        expect(msg["id"]).to_equal(7)
        expect(msg["type"]).to_equal(TYPE_RESULT)
        expect(msg["success"]).to_be_truthy()

        domains = [item["domain"] for item in msg["result"]]
        expect("discovered_integration" in domains).to_be_truthy()
        expect("user_flow_integration" in domains).to_be_falsy()


@test
async def integration_log_info_with_settings(
    _executor: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    hass_admin_user=Depends(hass_admin_user_fixture),
) -> None:
    """Test that log info includes integrations with custom log settings."""
    expect(await async_setup_component(hass, "logger", {})).to_be_truthy()

    mock_integration(hass, MockModule("unloaded_integration"))

    websocket_client = await hass_ws_client()
    await websocket_client.send_json(
        {
            "id": 1,
            "type": "logger/integration_log_level",
            "integration": "unloaded_integration",
            "level": "DEBUG",
            "persistence": "none",
        }
    )
    msg = await websocket_client.receive_json()
    expect(msg["success"]).to_be_truthy()

    await websocket_client.send_json({"id": 2, "type": "logger/log_info"})

    msg = await websocket_client.receive_json()
    expect(msg["id"]).to_equal(2)
    expect(msg["success"]).to_be_truthy()

    domains = [item["domain"] for item in msg["result"]]
    expect("unloaded_integration" in domains).to_be_truthy()


@test
async def integration_log_level_logger_not_loaded(
    _executor: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    hass_admin_user=Depends(hass_admin_user_fixture),
) -> None:
    """Test setting integration log level."""
    websocket_client = await hass_ws_client()
    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logger/log_level",
            "integration": "websocket_api",
            "level": logging.DEBUG,
            "persistence": "none",
        }
    )

    msg = await websocket_client.receive_json()
    expect(msg["id"]).to_equal(7)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_falsy()


@test
async def integration_log_level(
    _executor: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    hass_admin_user=Depends(hass_admin_user_fixture),
) -> None:
    """Test setting integration log level."""
    websocket_client = await hass_ws_client()
    expect(await async_setup_component(hass, "logger", {})).to_be_truthy()

    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logger/integration_log_level",
            "integration": "websocket_api",
            "level": "DEBUG",
            "persistence": "none",
        }
    )

    msg = await websocket_client.receive_json()
    expect(msg["id"]).to_equal(7)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()

    expect(hass.data[DATA_LOGGER].overrides).to_equal(
        {"homeassistant.components.websocket_api": logging.DEBUG}
    )


@test
async def custom_integration_log_level(
    _executor: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    hass_admin_user=Depends(hass_admin_user_fixture),
) -> None:
    """Test setting integration log level."""
    websocket_client = await hass_ws_client()
    expect(await async_setup_component(hass, "logger", {})).to_be_truthy()

    integration = loader.Integration(
        hass,
        "custom_components.hue",
        None,
        {
            "name": "Hue",
            "dependencies": [],
            "requirements": [],
            "domain": "hue",
            "loggers": ["some_other_logger"],
        },
    )

    with (
        patch(
            "homeassistant.components.logger.helpers.async_get_integration",
            return_value=integration,
        ),
        patch(
            "homeassistant.components.logger.websocket_api.async_get_integration",
            return_value=integration,
        ),
    ):
        await websocket_client.send_json(
            {
                "id": 7,
                "type": "logger/integration_log_level",
                "integration": "hue",
                "level": "DEBUG",
                "persistence": "none",
            }
        )

        msg = await websocket_client.receive_json()
        expect(msg["id"]).to_equal(7)
        expect(msg["type"]).to_equal(TYPE_RESULT)
        expect(msg["success"]).to_be_truthy()

        expect(hass.data[DATA_LOGGER].overrides).to_equal(
            {
                "homeassistant.components.hue": logging.DEBUG,
                "custom_components.hue": logging.DEBUG,
                "some_other_logger": logging.DEBUG,
            }
        )


@test
async def integration_log_level_unknown_integration(
    _executor: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    hass_admin_user=Depends(hass_admin_user_fixture),
) -> None:
    """Test setting integration log level for an unknown integration."""
    websocket_client = await hass_ws_client()
    expect(await async_setup_component(hass, "logger", {})).to_be_truthy()

    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logger/integration_log_level",
            "integration": "websocket_api_123",
            "level": "DEBUG",
            "persistence": "none",
        }
    )

    msg = await websocket_client.receive_json()
    expect(msg["id"]).to_equal(7)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_falsy()


@test
async def module_log_level(
    _executor: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    hass_admin_user=Depends(hass_admin_user_fixture),
) -> None:
    """Test setting integration log level."""
    websocket_client = await hass_ws_client()
    expect(
        await async_setup_component(
            hass,
            "logger",
            {"logger": {"logs": {"homeassistant.components.other_component": "warning"}}},
        )
    ).to_be_truthy()

    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logger/log_level",
            "module": "homeassistant.components.websocket_api",
            "level": "DEBUG",
            "persistence": "none",
        }
    )

    msg = await websocket_client.receive_json()
    expect(msg["id"]).to_equal(7)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()

    expect(hass.data[DATA_LOGGER].overrides).to_equal(
        {
            "homeassistant.components.websocket_api": logging.DEBUG,
            "homeassistant.components.other_component": logging.WARNING,
        }
    )


@test
async def module_log_level_override(
    _executor: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    hass_admin_user=Depends(hass_admin_user_fixture),
) -> None:
    """Test override yaml integration log level."""
    websocket_client = await hass_ws_client()
    expect(
        await async_setup_component(
            hass,
            "logger",
            {"logger": {"logs": {"homeassistant.components.websocket_api": "warning"}}},
        )
    ).to_be_truthy()

    expect(hass.data[DATA_LOGGER].overrides).to_equal(
        {"homeassistant.components.websocket_api": logging.WARNING}
    )

    await websocket_client.send_json(
        {
            "id": 6,
            "type": "logger/log_level",
            "module": "homeassistant.components.websocket_api",
            "level": "ERROR",
            "persistence": "none",
        }
    )

    msg = await websocket_client.receive_json()
    expect(msg["id"]).to_equal(6)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()

    expect(hass.data[DATA_LOGGER].overrides).to_equal(
        {"homeassistant.components.websocket_api": logging.ERROR}
    )

    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logger/log_level",
            "module": "homeassistant.components.websocket_api",
            "level": "DEBUG",
            "persistence": "none",
        }
    )

    msg = await websocket_client.receive_json()
    expect(msg["id"]).to_equal(7)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()

    expect(hass.data[DATA_LOGGER].overrides).to_equal(
        {"homeassistant.components.websocket_api": logging.DEBUG}
    )

    await websocket_client.send_json(
        {
            "id": 8,
            "type": "logger/log_level",
            "module": "homeassistant.components.websocket_api",
            "level": "NOTSET",
            "persistence": "none",
        }
    )

    msg = await websocket_client.receive_json()
    expect(msg["id"]).to_equal(8)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()

    expect(hass.data[DATA_LOGGER].overrides).to_equal(
        {"homeassistant.components.websocket_api": logging.NOTSET}
    )


@test
async def integration_log_level_requires_admin(
    _executor: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    hass_read_only_access_token: str = Depends(hass_read_only_access_token_fixture),
) -> None:
    """Test setting integration log level requires admin."""
    expect(await async_setup_component(hass, "logger", {})).to_be_truthy()

    websocket_client = await hass_ws_client(hass, hass_read_only_access_token)
    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logger/integration_log_level",
            "integration": "websocket_api",
            "level": "DEBUG",
            "persistence": "none",
        }
    )

    msg = await websocket_client.receive_json()
    expect(msg["success"]).to_be_falsy()
    expect(msg["error"]["code"]).to_equal("unauthorized")


@test
async def module_log_level_requires_admin(
    _executor: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    hass_read_only_access_token: str = Depends(hass_read_only_access_token_fixture),
) -> None:
    """Test setting module log level requires admin."""
    expect(await async_setup_component(hass, "logger", {})).to_be_truthy()

    websocket_client = await hass_ws_client(hass, hass_read_only_access_token)
    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logger/log_level",
            "module": "homeassistant.components.websocket_api",
            "level": "DEBUG",
            "persistence": "none",
        }
    )

    msg = await websocket_client.receive_json()
    expect(msg["success"]).to_be_falsy()
    expect(msg["error"]["code"]).to_equal("unauthorized")
