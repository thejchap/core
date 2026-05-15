"""Tests for Vanderbilt SPC component."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import mock_client

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def valid_device_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_client),
) -> None:
    """Test valid device config."""
    config = {"spc": {"api_url": "http://localhost/", "ws_url": "ws://localhost/"}}

    expect(await async_setup_component(hass, "spc", config)).to_be(True)


@test
async def invalid_device_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_client),
) -> None:
    """Test invalid device config."""
    config = {"spc": {"api_url": "http://localhost/"}}

    expect(await async_setup_component(hass, "spc", config)).to_be(False)


_ = (mock_client,)
