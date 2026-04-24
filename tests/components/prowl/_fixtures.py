"""Tryke fixtures for Prowl tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.notify import DOMAIN as NOTIFY_DOMAIN
from homeassistant.components.prowl.const import DOMAIN
from homeassistant.const import CONF_API_KEY, CONF_NAME

from tests.common import MockConfigEntry

TEST_NAME = "TestProwl"
TEST_SERVICE = TEST_NAME.lower()
ENTITY_ID = f"{NOTIFY_DOMAIN}.{TEST_SERVICE}"
TEST_API_KEY = "f00f" * 10
OTHER_API_KEY = "beef" * 10
CONF_INPUT = {CONF_API_KEY: TEST_API_KEY, CONF_NAME: TEST_NAME}
CONF_INPUT_NEW_KEY = {CONF_API_KEY: OTHER_API_KEY}
INVALID_API_KEY_ERROR = {"base": "invalid_api_key"}
TIMEOUT_ERROR = {"base": "api_timeout"}
BAD_API_RESPONSE = {"base": "bad_api_response"}


@fixture
def mock_prowlpy() -> Generator[AsyncMock]:
    """Mock the prowlpy library."""
    mock_instance = AsyncMock()

    with (
        patch(
            "homeassistant.components.prowl.notify.prowlpy.AsyncProwl",
            return_value=mock_instance,
        ),
        patch(
            "homeassistant.components.prowl.helpers.prowlpy.AsyncProwl",
            return_value=mock_instance,
        ),
        patch(
            "homeassistant.components.prowl.__init__.prowlpy.AsyncProwl",
            return_value=mock_instance,
        ),
    ):
        yield mock_instance


@fixture
def mock_prowlpy_config_entry() -> MockConfigEntry:
    """Fixture to create a mocked ConfigEntry."""
    return MockConfigEntry(
        title=TEST_NAME, domain=DOMAIN, data={CONF_API_KEY: TEST_API_KEY}
    )
