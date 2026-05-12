"""Tests for the Freebox utility methods."""

import json
from unittest.mock import Mock

from freebox_api.exceptions import HttpRequestError
from tryke import Depends, expect, fixture, test

from homeassistant.components.freebox.router import get_hosts_list_if_supported, is_json

from ._fixtures import (
    mock_router_bridge_mode_error as mock_router_bridge_mode_error_fixture,
    router as router_fixture,
    router_bridge_mode as router_bridge_mode_fixture,
)
from .const import DATA_LAN_GET_HOSTS_LIST_MODE_BRIDGE, DATA_WIFI_GET_GLOBAL_CONFIG


@fixture
def _trigger_executor() -> None:
    """Module-local resolution anchor — see PATTERNS.md."""


@test
async def is_json_check(_t: None = Depends(_trigger_executor)) -> None:
    """Test is_json method."""
    expect(is_json("{}")).to_be(True)
    expect(is_json('{ "simple":"json" }')).to_be(True)
    expect(is_json(json.dumps(DATA_WIFI_GET_GLOBAL_CONFIG))).to_be(True)
    expect(is_json(json.dumps(DATA_LAN_GET_HOSTS_LIST_MODE_BRIDGE))).to_be(True)

    expect(is_json(None)).to_be(False)
    expect(is_json("")).to_be(False)
    expect(is_json("XXX")).to_be(False)
    expect(is_json("{XXX}")).to_be(False)


@test
async def get_hosts_list_if_supported_router_mode(
    _t: None = Depends(_trigger_executor),
    router: Mock = Depends(router_fixture),
) -> None:
    """In router mode, get_hosts_list is supported and list is filled."""
    supports_hosts, fbx_devices = await get_hosts_list_if_supported(router())
    expect(supports_hosts).to_be(True)
    expect(bool(fbx_devices)).to_be(True)
    expect(len(fbx_devices)).to_equal(5)
    expect("d633d0c8-958c-43cc-e807-d881b076924b" in str(fbx_devices)).to_be(True)
    expect("d633d0c8-958c-42cc-e807-d881b476924b" in str(fbx_devices)).to_be(True)


@test
async def get_hosts_list_if_supported_bridge_mode(
    _t: None = Depends(_trigger_executor),
    router_bridge_mode: Mock = Depends(router_bridge_mode_fixture),
) -> None:
    """In bridge mode, get_hosts_list is NOT supported and list is empty."""
    supports_hosts, fbx_devices = await get_hosts_list_if_supported(
        router_bridge_mode()
    )
    expect(supports_hosts).to_be(False)
    expect(fbx_devices).to_equal([])


@test
async def get_hosts_list_if_supported_bridge_error(
    _t: None = Depends(_trigger_executor),
    mock_router_bridge_mode_error: Mock = Depends(mock_router_bridge_mode_error_fixture),
) -> None:
    """Other exceptions must be propagated."""
    raised: HttpRequestError | None = None
    try:
        await get_hosts_list_if_supported(mock_router_bridge_mode_error())
    except HttpRequestError as err:
        raised = err
    expect(raised is not None).to_be(True)
