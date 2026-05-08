"""Tryke fixtures for the Telegram Bot integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.telegram_bot.const import (
    ATTR_PARSER,
    CONF_ALLOWED_CHAT_IDS,
    CONF_API_ENDPOINT,
    CONF_CHAT_ID,
    CONF_TRUSTED_NETWORKS,
    DOMAIN,
    PARSER_MD,
    PLATFORM_WEBHOOKS,
)
from homeassistant.config_entries import ConfigSubentryData
from homeassistant.const import CONF_API_KEY, CONF_PLATFORM, CONF_URL

from tests.common import MockConfigEntry


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.telegram_bot.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_webhooks_config_entry() -> MockConfigEntry:
    """Return a mocked webhooks config entry."""
    return MockConfigEntry(
        unique_id="mock api key",
        domain=DOMAIN,
        data={
            CONF_PLATFORM: PLATFORM_WEBHOOKS,
            CONF_API_KEY: "mock api key",
            CONF_URL: "https://test",
            CONF_API_ENDPOINT: "http://mock/bot",
            CONF_TRUSTED_NETWORKS: ["127.0.0.1"],
        },
        options={ATTR_PARSER: PARSER_MD},
        subentries_data=[
            ConfigSubentryData(
                unique_id="12345678",
                data={CONF_CHAT_ID: 12345678},
                subentry_type=CONF_ALLOWED_CHAT_IDS,
                title="mock chat",
            )
        ],
        minor_version=2,
    )
