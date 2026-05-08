"""Tryke fixtures for the SolarEdge integration."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock, patch

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_recorder_mock


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.solaredge.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def solaredge_api() -> Generator[Mock]:
    """Mock a successful SolarEdge Monitoring API."""
    api = Mock()
    api.get_details = AsyncMock(return_value={"details": {"status": "active"}})
    with (
        patch(
            "homeassistant.components.solaredge.config_flow.aiosolaredge.SolarEdge",
            return_value=api,
        ),
        patch(
            "homeassistant.components.solaredge.SolarEdge",
            return_value=api,
        ),
    ):
        yield api


@fixture
def solaredge_web_api() -> Generator[AsyncMock]:
    """Mock a successful SolarEdge Web API."""
    with (
        patch(
            "homeassistant.components.solaredge.config_flow.SolarEdgeWeb", autospec=True
        ) as mock_web_api_flow,
        patch(
            "homeassistant.components.solaredge.coordinator.SolarEdgeWeb", autospec=True
        ) as mock_web_api_coord,
    ):
        api = mock_web_api_flow.return_value
        mock_web_api_coord.return_value = api
        api.async_get_equipment.return_value = {
            1001: {"displayName": "1.1"},
            1002: {"displayName": "1.2"},
        }
        yield api


@fixture
async def recorder_mock(
    hass: HomeAssistant = Depends(hass_fixture),
) -> AsyncGenerator[object]:
    """Set up an in-memory recorder for solaredge flow tests."""
    instance = await setup_recorder_mock(hass)
    yield instance
