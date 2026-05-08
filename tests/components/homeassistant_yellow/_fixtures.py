"""Tryke fixtures for the homeassistant_yellow integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from aiohasupervisor import SupervisorClient
from tryke import Depends, fixture


@fixture
def supervisor_client() -> Generator[AsyncMock]:
    """Mock the supervisor client (trimmed for Yellow surface area)."""
    supervisor_client = AsyncMock(spec=SupervisorClient)
    supervisor_client.os = AsyncMock()
    supervisor_client.host = AsyncMock()

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
    """Mock the yellow-config-flow's get_supervisor_client lookup."""
    with patch(
        "homeassistant.components.homeassistant_yellow.config_flow.get_supervisor_client",
        return_value=supervisor_client,
    ):
        yield


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override the homeassistant_yellow async_setup_entry."""
    with patch(
        "homeassistant.components.homeassistant_yellow.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_addon_state_wait() -> Generator[None]:
    """Mock WaitingAddonManager.async_wait_until_addon_state."""
    with patch(
        "homeassistant.components.homeassistant_hardware.silabs_multiprotocol_addon.WaitingAddonManager.async_wait_until_addon_state"
    ):
        yield
