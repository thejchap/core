"""Tryke fixtures for the Home Assistant Green integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from aiohasupervisor import SupervisorClient
from tryke import Depends, fixture


@fixture
def supervisor_client() -> Generator[AsyncMock]:
    """Mock the supervisor client (trimmed to the surface used by Green)."""
    supervisor_client = AsyncMock(spec=SupervisorClient)
    supervisor_client.os = AsyncMock()

    with (
        patch(
            "homeassistant.components.hassio.get_supervisor_client",
            return_value=supervisor_client,
        ),
        patch(
            "homeassistant.components.hassio.handler.get_supervisor_client",
            return_value=supervisor_client,
        ),
    ):
        yield supervisor_client


@fixture
def mock_get_supervisor_client(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> Generator[None]:
    """Mock the green-config-flow's get_supervisor_client lookup."""
    with patch(
        "homeassistant.components.homeassistant_green.config_flow.get_supervisor_client",
        return_value=supervisor_client,
    ):
        yield


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override the homeassistant_green async_setup_entry."""
    with patch(
        "homeassistant.components.homeassistant_green.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry
