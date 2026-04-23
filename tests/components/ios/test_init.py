"""Tests for the iOS init file."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import ios
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import mock_component
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@fixture
def mock_load_json() -> Generator[None]:
    """Mock load_json."""
    with patch("homeassistant.components.ios.load_json_object", return_value={}):
        yield


@fixture
def mock_dependencies(hass: HomeAssistant = Depends(hass)) -> None:
    """Mock dependencies loaded."""
    mock_component(hass, "zeroconf")
    mock_component(hass, "device_tracker")


@test
async def creating_entry_sets_up_sensor(
    hass: HomeAssistant = Depends(hass),
    _mock_load_json: None = Depends(mock_load_json),
    _mock_deps: None = Depends(mock_dependencies),
) -> None:
    """Test setting up iOS loads the sensor component."""
    with patch(
        "homeassistant.components.ios.sensor.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        result = await async_setup_component(hass, ios.DOMAIN, {ios.DOMAIN: {}})
        expect(result).to_be(True)
        await hass.async_block_till_done()

    expect(len(mock_setup.mock_calls)).to_equal(1)


@test
async def configuring_ios_creates_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_load_json: None = Depends(mock_load_json),
    _mock_deps: None = Depends(mock_dependencies),
) -> None:
    """Test that specifying config will create an entry."""
    with patch(
        "homeassistant.components.ios.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        await async_setup_component(hass, ios.DOMAIN, {"ios": {"push": {}}})
        await hass.async_block_till_done()

    expect(len(mock_setup.mock_calls)).to_equal(1)


@test
async def not_configuring_ios_not_creates_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_load_json: None = Depends(mock_load_json),
    _mock_deps: None = Depends(mock_dependencies),
) -> None:
    """Test that no config will not create an entry."""
    with patch(
        "homeassistant.components.ios.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        await async_setup_component(hass, ios.DOMAIN, {"foo": "bar"})
        await hass.async_block_till_done()

    expect(len(mock_setup.mock_calls)).to_equal(0)
