"""Tryke fixtures for conversation tests."""

from __future__ import annotations

from collections.abc import Generator
import logging
from typing import Any
from unittest.mock import Mock, patch

from tryke import Depends, fixture

from homeassistant.components import conversation
from homeassistant.components.conversation import async_get_agent, default_agent
from homeassistant.const import MATCH_ALL
from homeassistant.core import Context, HomeAssistant, ServiceCall, ServiceResponse
from homeassistant.exceptions import ServiceNotFound
from homeassistant.setup import async_setup_component

from . import MockAgent

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

_LOGGER = logging.getLogger(__name__)


@fixture
def mock_ulid() -> Generator[Mock]:
    """Mock the ulid library."""
    with patch("homeassistant.helpers.chat_session.ulid_now") as mock_ulid_now:
        mock_ulid_now.return_value = "mock-ulid"
        yield mock_ulid_now


@fixture
def mock_agent_support_all(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockAgent:
    """Mock agent that supports all languages."""
    entry = MockConfigEntry(entry_id="mock-entry-support-all")
    entry.add_to_hass(hass)
    agent = MockAgent(entry.entry_id, MATCH_ALL)
    conversation.async_set_agent(hass, entry, agent)
    return agent


@fixture
def mock_conversation_input(
    hass: HomeAssistant = Depends(hass_fixture),
) -> conversation.ConversationInput:
    """Return a conversation input instance."""
    return conversation.ConversationInput(
        text="Hello",
        context=Context(),
        conversation_id=None,
        agent_id="mock-agent-id",
        device_id=None,
        satellite_id=None,
        language="en",
    )


@fixture
def mock_shopping_list_io() -> Generator[None]:
    """Stub out the persistence."""
    with (
        patch("homeassistant.components.shopping_list.ShoppingData.save"),
        patch("homeassistant.components.shopping_list.ShoppingData.async_load"),
    ):
        yield


@fixture
def service_calls(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[list[ServiceCall]]:
    """Track all service calls."""
    calls: list[ServiceCall] = []

    _original_async_call = hass.services.async_call

    async def _async_call(
        self,
        domain: str,
        service: str,
        service_data: dict[str, Any] | None = None,
        blocking: bool = False,
        context: Context | None = None,
        target: dict[str, Any] | None = None,
        return_response: bool = False,
    ) -> ServiceResponse:
        calls.append(
            ServiceCall(hass, domain, service, service_data, context, return_response)
        )
        try:
            return await _original_async_call(
                domain,
                service,
                service_data,
                blocking,
                context,
                target,
                return_response,
            )
        except ServiceNotFound:
            _LOGGER.debug("Ignoring unknown service call to %s.%s", domain, service)
        return None

    with patch("homeassistant.core.ServiceRegistry.async_call", _async_call):
        yield calls


@fixture
async def init_components(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Initialize relevant components with empty configs."""
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(
        hass, "conversation", {conversation.DOMAIN: {}}
    )
    agent = async_get_agent(hass)
    assert isinstance(agent, default_agent.DefaultAgent)
    agent.fuzzy_matching = False
