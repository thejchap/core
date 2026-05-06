"""Tryke fixtures for Rehlko integration tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from tryke import Depends, fixture

from homeassistant.components.rehlko import DOMAIN
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from tests.common import MockConfigEntry, load_json_value_fixture

TEST_EMAIL = "MyEmail@email.com"
TEST_PASSWORD = "password"
TEST_SUBJECT = TEST_EMAIL.lower()
TEST_REFRESH_TOKEN = "my_refresh_token"


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.rehlko.async_setup_entry", return_value=True
    ) as m:
        yield m


@fixture
def homes() -> list[dict[str, Any]]:
    """Create rehlko homes fixture."""
    return load_json_value_fixture("homes.json", DOMAIN)


@fixture
def generator() -> dict[str, Any]:
    """Create rehlko generator fixture."""
    return load_json_value_fixture("generator.json", DOMAIN)


@fixture
def rehlko_config_entry() -> MockConfigEntry:
    """Create a config entry fixture."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD},
        unique_id=TEST_SUBJECT,
    )


@fixture
async def mock_rehlko(
    rehlko_homes: list[dict[str, Any]] = Depends(homes),
    rehlko_generator: dict[str, Any] = Depends(generator),
) -> AsyncGenerator[AsyncMock]:
    """Mock Rehlko instance."""
    with (
        patch("homeassistant.components.rehlko.AioKem", autospec=True) as mock_kem,
        patch("homeassistant.components.rehlko.config_flow.AioKem", new=mock_kem),
    ):
        client = mock_kem.return_value
        client.get_homes = AsyncMock(return_value=rehlko_homes)
        client.get_generator_data = AsyncMock(return_value=rehlko_generator)
        client.authenticate = AsyncMock(return_value=None)
        client.get_token_subject = Mock(return_value=TEST_SUBJECT)
        client.get_refresh_token = AsyncMock(return_value=TEST_REFRESH_TOKEN)
        client.set_refresh_token_callback = Mock()
        client.set_retry_policy = Mock()
        yield client
