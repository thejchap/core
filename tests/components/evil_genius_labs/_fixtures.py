"""Tryke fixtures for the Evil Genius Labs integration."""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util.json import JsonObjectType

from tests.common import (
    MockConfigEntry,
    load_json_array_fixture,
    load_json_object_fixture,
)
from tests.hass_fixtures import hass as hass_fixture


@fixture
def all_fixture() -> dict[str, Any]:
    """Fixture data."""
    data = load_json_array_fixture("data.json", "evil_genius_labs")
    return {item["name"]: item for item in data}


@fixture
def info_fixture() -> JsonObjectType:
    """Fixture info."""
    return load_json_object_fixture("info.json", "evil_genius_labs")


@fixture
def product_fixture() -> dict[str, str]:
    """Fixture info."""
    return {"productName": "Fibonacci256"}


@fixture
def platforms_fixture() -> list[Platform]:
    """Default platforms (override per test if needed)."""
    from homeassistant.components.evil_genius_labs import PLATFORMS  # noqa: PLC0415

    return PLATFORMS


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Evil genius labs config entry."""
    entry = MockConfigEntry(domain="evil_genius_labs", data={"host": "192.168.1.113"})
    entry.add_to_hass(hass)
    return entry


@fixture
async def setup_evil_genius_labs(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry),
    all_data: dict[str, Any] = Depends(all_fixture),
    info: JsonObjectType = Depends(info_fixture),
    product: dict[str, str] = Depends(product_fixture),
    platforms: list[Platform] = Depends(platforms_fixture),
) -> AsyncGenerator[None]:
    """Set up Evil Genius Labs instance."""
    with (
        patch(
            "pyevilgenius.EvilGeniusDevice.get_all",
            return_value=all_data,
        ),
        patch(
            "pyevilgenius.EvilGeniusDevice.get_info",
            return_value=info,
        ),
        patch(
            "pyevilgenius.EvilGeniusDevice.get_product",
            return_value=product,
        ),
        patch(
            "homeassistant.components.evil_genius_labs.PLATFORMS",
            platforms,
        ),
    ):
        assert await async_setup_component(hass, "evil_genius_labs", {})
        await hass.async_block_till_done()
        yield
