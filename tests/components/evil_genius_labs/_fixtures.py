"""Tryke fixtures for the Evil Genius Labs integration."""

from typing import Any

from tryke import fixture

from homeassistant.util.json import JsonObjectType

from tests.common import load_json_array_fixture, load_json_object_fixture


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
