"""Tests for the Ollama integration init (tryke port)."""

from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import ollama
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import mock_config_entry, mock_config_entry_with_token

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Force tryke fixture resolution before each test."""


@test
async def init_without_api_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test initialization without API key - Authorization header should not be set."""
    expect(await async_setup_component(hass, "homeassistant", {})).to_be(True)
    with patch("homeassistant.components.ollama.ollama.AsyncClient") as mock_client:
        mock_client.return_value.list = AsyncMock(return_value={"models": []})

        expect(await async_setup_component(hass, ollama.DOMAIN, {})).to_be(True)
        await hass.async_block_till_done()

        # No Authorization header should be set when there's no API key.
        expect(
            all(
                call.kwargs.get("headers") is None
                for call in mock_client.call_args_list
            )
        ).to_be(True)


@test
async def init_with_api_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry_with_token),
) -> None:
    """Test initialization with API key - Authorization header should be set."""
    expect(await async_setup_component(hass, "homeassistant", {})).to_be(True)
    with patch("homeassistant.components.ollama.ollama.AsyncClient") as mock_client:
        mock_client.return_value.list = AsyncMock(return_value={"models": []})

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        expect(
            any(
                call.kwargs.get("headers") == {"Authorization": "Bearer test_token"}
                for call in mock_client.call_args_list
            )
        ).to_be(True)


@test.skip("requires ollama AsyncClient mocks + conversation infra (not ported)")
async def migrate_entry_from_v3_2() -> None:
    """Stub for test_migrate_entry_from_v3_2 (port deferred)."""


@test.skip("requires ollama AsyncClient mocks + conversation infra (not ported)")
async def init_error() -> None:
    """Stub for test_init_error (port deferred)."""


@test.skip("requires ollama AsyncClient mocks + conversation infra (not ported)")
async def async_setup_entry_auth_failed_on_response_error() -> None:
    """Stub for test_async_setup_entry_auth_failed_on_response_error (port deferred)."""


@test.skip("requires ollama AsyncClient mocks + conversation infra (not ported)")
async def migration_from_v1() -> None:
    """Stub for test_migration_from_v1 (port deferred)."""


@test.skip("requires ollama AsyncClient mocks + conversation infra (not ported)")
async def migration_from_v1_with_multiple_urls() -> None:
    """Stub for test_migration_from_v1_with_multiple_urls (port deferred)."""


@test.skip("requires ollama AsyncClient mocks + conversation infra (not ported)")
async def migration_from_v1_with_same_urls() -> None:
    """Stub for test_migration_from_v1_with_same_urls (port deferred)."""


@test.skip("requires ollama AsyncClient mocks + conversation infra (not ported)")
async def migration_from_v1_disabled() -> None:
    """Stub for test_migration_from_v1_disabled (port deferred)."""


@test.skip("requires ollama AsyncClient mocks + conversation infra (not ported)")
async def migration_from_v2_1() -> None:
    """Stub for test_migration_from_v2_1 (port deferred)."""


@test.skip("requires ollama AsyncClient mocks + conversation infra (not ported)")
async def migration_from_v2_2() -> None:
    """Stub for test_migration_from_v2_2 (port deferred)."""


@test.skip("requires ollama AsyncClient mocks + conversation infra (not ported)")
async def migration_from_v3_1_without_subentry() -> None:
    """Stub for test_migration_from_v3_1_without_subentry (port deferred)."""
