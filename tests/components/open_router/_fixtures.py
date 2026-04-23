"""Tryke fixtures for OpenRouter integration tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from python_open_router import KeyData, ModelsDataWrapper
from tryke import Depends, fixture

from homeassistant.components.open_router.const import (
    CONF_PROMPT,
    CONF_WEB_SEARCH,
    DOMAIN,
)
from homeassistant.config_entries import ConfigSubentryData
from homeassistant.const import CONF_API_KEY, CONF_LLM_HASS_API, CONF_MODEL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry, async_load_fixture
from tests.hass_fixtures import hass as hass_fixture


def make_conversation_subentry_data(
    enable_assist: bool = False, web_search: bool = False
) -> dict[str, Any]:
    """Build conversation subentry data."""
    res: dict[str, Any] = {
        CONF_MODEL: "openai/gpt-3.5-turbo",
        CONF_PROMPT: "You are a helpful assistant.",
        CONF_WEB_SEARCH: web_search,
    }
    if enable_assist:
        res[CONF_LLM_HASS_API] = [llm.LLM_API_ASSIST]
    return res


def make_ai_task_subentry_data() -> dict[str, Any]:
    """Build AI task subentry data."""
    return {CONF_MODEL: "google/gemini-1.5-pro"}


def make_mock_config_entry(
    enable_assist: bool = False, web_search: bool = False
) -> MockConfigEntry:
    """Build a MockConfigEntry with the two default subentries."""
    return MockConfigEntry(
        title="OpenRouter",
        domain=DOMAIN,
        data={CONF_API_KEY: "bla"},
        subentries_data=[
            ConfigSubentryData(
                data=make_conversation_subentry_data(
                    enable_assist=enable_assist, web_search=web_search
                ),
                subentry_id="ABCDEF",
                subentry_type="conversation",
                title="GPT-3.5 Turbo",
                unique_id=None,
            ),
            ConfigSubentryData(
                data=make_ai_task_subentry_data(),
                subentry_id="ABCDEG",
                subentry_type="ai_task_data",
                title="Gemini 1.5 Pro",
                unique_id=None,
            ),
        ],
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.open_router.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Default MockConfigEntry."""
    return make_mock_config_entry()


@fixture
async def mock_openai_client() -> AsyncGenerator[AsyncMock]:
    """Mock the AsyncOpenAI client."""
    with patch("homeassistant.components.open_router.AsyncOpenAI") as mock_client:
        client = mock_client.return_value
        client.chat.completions.create = AsyncMock(
            return_value=ChatCompletion(
                id="chatcmpl-1234567890ABCDEFGHIJKLMNOPQRS",
                choices=[
                    Choice(
                        finish_reason="stop",
                        index=0,
                        message=ChatCompletionMessage(
                            content="Hello, how can I help you?",
                            role="assistant",
                            function_call=None,
                            tool_calls=None,
                        ),
                    )
                ],
                created=1700000000,
                model="gpt-3.5-turbo-0613",
                object="chat.completion",
                system_fingerprint=None,
                usage=CompletionUsage(
                    completion_tokens=9, prompt_tokens=8, total_tokens=17
                ),
            )
        )
        yield client


@fixture
async def mock_open_router_client(
    hass: HomeAssistant = Depends(hass_fixture),
) -> AsyncGenerator[AsyncMock]:
    """Mock the OpenRouter client."""
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
async def setup_ha(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Ensure the homeassistant component is set up."""
    await async_setup_component(hass, "homeassistant", {})


@fixture
def mock_zeroconf() -> Generator[MagicMock]:
    """Mock zeroconf to avoid real network singletons leaking between tests."""
    from zeroconf import DNSCache, Zeroconf
    from zeroconf.asyncio import AsyncZeroconf

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch(
            "homeassistant.components.zeroconf.discovery.AsyncServiceBrowser",
        ) as mock_browser,
        patch(
            "homeassistant.components.zeroconf.HaAsyncZeroconf",
            spec=AsyncZeroconf,
        ) as mock_aiozc,
    ):
        asb = mock_browser.return_value
        asb.async_cancel = AsyncMock()
        zc = mock_zc.return_value
        zc.cache = DNSCache()

        aiozc = mock_aiozc.return_value
        aiozc.async_unregister_service = AsyncMock()
        aiozc.async_register_service = AsyncMock()
        aiozc.async_update_service = AsyncMock()
        aiozc.zeroconf = Mock(spec=Zeroconf)
        aiozc.zeroconf.async_wait_for_start = AsyncMock()
        aiozc.zeroconf.cache = DNSCache()
        aiozc.zeroconf.done = False
        aiozc.async_close = AsyncMock()
        aiozc.ha_async_close = AsyncMock()
        yield mock_zc
