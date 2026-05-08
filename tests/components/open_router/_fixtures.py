"""Tryke fixtures for the OpenRouter integration."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

from python_open_router import KeyData, ModelsDataWrapper
from tryke import Depends, fixture

from homeassistant.components.open_router.const import DOMAIN
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, async_load_fixture
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.open_router.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
async def mock_open_router_client(
    hass: HomeAssistant = Depends(hass_fixture),
) -> AsyncGenerator[AsyncMock]:
    """Mock OpenRouter client."""
    with patch(
        "homeassistant.components.open_router.config_flow.OpenRouterClient",
        autospec=True,
    ) as mock_client:
        client = mock_client.return_value
        client.get_key_data.return_value = KeyData(
            label="Test account",
            usage=0,
            is_provisioning_key=False,
            limit_remaining=None,
            is_free_tier=True,
        )
        models = await async_load_fixture(hass, "models.json", DOMAIN)
        client.get_models.return_value = ModelsDataWrapper.from_json(models).data
        yield client


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        title="OpenRouter",
        domain=DOMAIN,
        data={CONF_API_KEY: "bla"},
    )
