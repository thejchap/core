"""Tryke fixtures for ScreenLogic integration tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import Mock, patch

from tryke import fixture

from homeassistant.components.screenlogic import DOMAIN
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT, CONF_SCAN_INTERVAL

from . import (
    MOCK_ADAPTER_IP,
    MOCK_ADAPTER_MAC,
    MOCK_ADAPTER_NAME,
    MOCK_ADAPTER_PORT,
    MOCK_CONFIG_ENTRY_ID,
)

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mocked config entry."""
    return MockConfigEntry(
        title=MOCK_ADAPTER_NAME,
        domain=DOMAIN,
        data={
            CONF_IP_ADDRESS: MOCK_ADAPTER_IP,
            CONF_PORT: MOCK_ADAPTER_PORT,
        },
        options={
            CONF_SCAN_INTERVAL: 30,
        },
        unique_id=MOCK_ADAPTER_MAC,
        entry_id=MOCK_CONFIG_ENTRY_ID,
    )


@fixture
def mock_disconnect() -> Generator[None]:
    """Mock disconnect for all tests."""

    async def _subscribe_client(*args, **kwargs):
        """Mock subscribe client."""
        return Mock()

    with patch(
        "homeassistant.components.screenlogic.ScreenLogicGateway.async_subscribe_client",
        _subscribe_client,
    ):
        yield
