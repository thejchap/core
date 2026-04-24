"""Tryke fixtures for qbus tests."""

from __future__ import annotations

from tryke import fixture

from homeassistant.components.qbus.const import DOMAIN
from homeassistant.util.json import JsonObjectType

from .const import FIXTURE_PAYLOAD_CONFIG

from tests.common import load_json_object_fixture


@fixture
def payload_config() -> JsonObjectType:
    """Return the config topic payload."""
    return load_json_object_fixture(FIXTURE_PAYLOAD_CONFIG, DOMAIN)
