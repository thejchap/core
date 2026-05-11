"""Test Hue bridge."""

import asyncio
from unittest.mock import Mock, patch

from aiohttp import client_exceptions
from aiohue.errors import Unauthorized
from aiohue.v1 import HueBridgeV1
from aiohue.v2 import HueBridgeV2
from tryke import Depends, expect, fixture, test

from homeassistant.components.hue import bridge
from homeassistant.components.hue.const import (
    CONF_ALLOW_HUE_GROUPS,
    CONF_ALLOW_UNREACHABLE,
    DOMAIN,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .conftest import create_mock_api_v1, create_mock_api_v2

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def mock_api_v1() -> Mock:
    """Mock the Hue V1 api."""
    return create_mock_api_v1()


@fixture
def mock_api_v2() -> Mock:
    """Mock the Hue V2 api."""
    return create_mock_api_v2()


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def bridge_setup_v1(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_api_v1: Mock = Depends(mock_api_v1),
) -> None:
    """Test a successful setup for V1 bridge."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "1.2.3.4", "api_key": "mock-api-key", "api_version": 1},
        options={CONF_ALLOW_HUE_GROUPS: False, CONF_ALLOW_UNREACHABLE: False},
    )

    with (
        patch.object(bridge, "HueBridgeV1", return_value=mock_api_v1),
        patch.object(hass.config_entries, "async_forward_entry_setups") as mock_forward,
    ):
        hue_bridge = bridge.HueBridge(hass, config_entry)
        async with config_entry.setup_lock:
            expect(await hue_bridge.async_initialize_bridge()).to_be(True)

    expect(hue_bridge.api).to_be(mock_api_v1)
    expect(isinstance(hue_bridge.api, HueBridgeV1)).to_be(True)
    expect(hue_bridge.api_version).to_equal(1)
    expect(len(mock_forward.mock_calls)).to_equal(1)
    forward_entries = set(mock_forward.mock_calls[0][1][1])
    expect(forward_entries).to_equal({"light", "binary_sensor", "sensor"})


@test
async def bridge_setup_v2(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_api_v2: Mock = Depends(mock_api_v2),
) -> None:
    """Test a successful setup for V2 bridge."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "1.2.3.4", "api_key": "mock-api-key", "api_version": 2},
    )

    with (
        patch.object(bridge, "HueBridgeV2", return_value=mock_api_v2),
        patch.object(hass.config_entries, "async_forward_entry_setups") as mock_forward,
    ):
        hue_bridge = bridge.HueBridge(hass, config_entry)
        expect(await hue_bridge.async_initialize_bridge()).to_be(True)

    expect(hue_bridge.api).to_be(mock_api_v2)
    expect(isinstance(hue_bridge.api, HueBridgeV2)).to_be(True)
    expect(hue_bridge.api_version).to_equal(2)
    expect(len(mock_forward.mock_calls)).to_equal(1)
    forward_entries = set(mock_forward.mock_calls[0][1][1])
    expect(forward_entries).to_equal(
        {
            "light",
            "binary_sensor",
            "event",
            "sensor",
            "switch",
            "scene",
        }
    )


@test
async def bridge_setup_invalid_api_key(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we start config flow if username is no longer whitelisted."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "1.2.3.4", "api_key": "mock-api-key", "api_version": 1},
        options={CONF_ALLOW_HUE_GROUPS: False, CONF_ALLOW_UNREACHABLE: False},
    )
    hue_bridge = bridge.HueBridge(hass, entry)

    with (
        patch.object(hue_bridge.api, "initialize", side_effect=Unauthorized),
        patch.object(hass.config_entries.flow, "async_init") as mock_init,
    ):
        expect(await hue_bridge.async_initialize_bridge()).to_be(False)

    expect(len(mock_init.mock_calls)).to_equal(1)
    expect(mock_init.mock_calls[0][2]["data"]).to_equal({"host": "1.2.3.4"})


@test
async def bridge_setup_timeout(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we retry to connect if we cannot connect."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "1.2.3.4", "api_key": "mock-api-key", "api_version": 1},
        options={CONF_ALLOW_HUE_GROUPS: False, CONF_ALLOW_UNREACHABLE: False},
    )
    hue_bridge = bridge.HueBridge(hass, entry)

    with patch.object(
        hue_bridge.api,
        "initialize",
        side_effect=client_exceptions.ServerDisconnectedError,
    ):
        async with expect_raises_async(ConfigEntryNotReady):
            await hue_bridge.async_initialize_bridge()


@test
async def reset_unloads_entry_if_setup(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_api_v1: Mock = Depends(mock_api_v1),
) -> None:
    """Test calling reset while the entry has been setup."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "1.2.3.4", "api_key": "mock-api-key", "api_version": 1},
        options={CONF_ALLOW_HUE_GROUPS: False, CONF_ALLOW_UNREACHABLE: False},
    )

    with (
        patch.object(bridge, "HueBridgeV1", return_value=mock_api_v1),
        patch.object(hass.config_entries, "async_forward_entry_setups") as mock_forward,
    ):
        hue_bridge = bridge.HueBridge(hass, config_entry)
        async with config_entry.setup_lock:
            expect(await hue_bridge.async_initialize_bridge()).to_be(True)

    await asyncio.sleep(0)

    expect(len(hass.services.async_services())).to_equal(0)
    expect(len(mock_forward.mock_calls)).to_equal(1)

    with patch.object(
        hass.config_entries, "async_forward_entry_unload", return_value=True
    ) as mock_forward:
        expect(await hue_bridge.async_reset()).to_be(True)

    expect(len(mock_forward.mock_calls)).to_equal(3)
    expect(len(hass.services.async_services())).to_equal(0)


@test
async def handle_unauthorized(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_api_v1: Mock = Depends(mock_api_v1),
) -> None:
    """Test handling an unauthorized error on update."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "1.2.3.4", "api_key": "mock-api-key", "api_version": 1},
        options={CONF_ALLOW_HUE_GROUPS: False, CONF_ALLOW_UNREACHABLE: False},
    )

    with patch.object(bridge, "HueBridgeV1", return_value=mock_api_v1):
        hue_bridge = bridge.HueBridge(hass, config_entry)
        async with config_entry.setup_lock:
            expect(await hue_bridge.async_initialize_bridge()).to_be(True)

    with patch.object(bridge, "create_config_flow") as mock_create:
        await hue_bridge.handle_unauthorized_error()

    expect(hue_bridge.authorized).to_be(False)
    expect(len(mock_create.mock_calls)).to_equal(1)
    expect(mock_create.mock_calls[0][1][1]).to_equal("1.2.3.4")
